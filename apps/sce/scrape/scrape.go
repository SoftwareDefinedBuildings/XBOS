/*
 go build -o sceconfirmed
 ./sceconfirmed

 This program runs periodically & checks for a confirmed SCE CPP event by scraping SCE's website

 If there is an event:
     it uses AWS SNS to notify everyone on the AWS SCE user topic
 If the is an error (e.g., error parsing):
     it will notify everyone on the AWS developer topic

This program also publishes a message to a BW topic in the SCE namespace
	 	following the i.xbos.demand_response_confirmed interface

This program can be configured to run during a predefined period
 	(e.g., once every 24 hours)
This program can also be configured to retry multiple times during that period
 	This is useful in case the signal is pushed later in the day
	(e.g., try 3 times (once every 2 hours) during a 24 hour period)

*/

package main

import (
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/sns"
	"golang.org/x/net/html"
	"gopkg.in/immesys/bw2bind.v5"
)

// configuration file path and variable
const confPath = "./config.json"

var config Config

// if already notified skip to next day
var notified bool

// BOSSWAVE client
var bw2client *bw2bind.BW2Client

// time format for notification
const layout = "02/01/2006"

type Config struct {
	Usrtopic            string //AWS user SNS topic
	Usrtopicregion      string //AWS user SNS topic region
	Devtopic            string //AWS developer SNS topic
	Devtopicregion      string //AWS developer SNS topic region
	Disablenotification bool   //set true to disable SNS notification
	DisableBWPublish    bool   //set to true to disable publishing events to BW
	BWPubtopic          string //BOSSWAVE PGE topic (e.g.,pge/confirmed/demand_response/)
	Sceurl              string //URL for SCE CPP website
	Period              int    //Overall period in hours to repeat notification (e.g., 24 hours)
	RetriesPerPeriod    int    //Max number of retries per period
	RetryInterval       int    //Wait time in hours between retries
}

// Event structure for publishing to the SCE Confirmed DR topic
type Event struct {
	Event_status int64
	Date         int64
	Time         int64
}

func main() {
	httpclient := &http.Client{Timeout: 10 * time.Second}
	configure()
Main:
	for {
		//reload config file in case settings changed
		loadConfigFile()
		for i := 0; i < config.RetriesPerPeriod; i++ {
			start := time.Now()
			// request and parse the front page
			resp, err := httpclient.Get(config.Sceurl)
			if err != nil {
				notify("Error: failed to GET main website from SCE: "+err.Error(), config.Devtopic, config.Devtopicregion)
				break Main
			}
			defer resp.Body.Close()
			if resp.StatusCode != 200 {
				notify("Error: GET status code is: "+strconv.Itoa(resp.StatusCode), config.Devtopic, config.Devtopicregion)
				break Main
			}

			z := html.NewTokenizer(resp.Body)
		Parse:
			for {
				tt := z.Next()
				switch tt {
				case html.ErrorToken:
					// End of the document, we're done
					break Parse
				case html.StartTagToken:
					t := z.Token()
					for _, a := range t.Attr {
						if a.Val == "rich-table EvtTable" {
							parseTable(z)
						}
					}
				}
			}
			elapsed := time.Since(start)
			if notified {
				// repeat the next day
				time.Sleep(time.Duration(config.Period-(i*config.RetryInterval))*time.Hour - elapsed)
				continue Main
			}
			// nothing is confirmed for tomorrow publish no event and try again later
			evt := time.Date(start.Year(), start.Month(), start.Day()+1, 0, 0, 0, 0, time.Local)
			publishEvent(Event{0, evt.UnixNano(), time.Now().UnixNano()})

			// run this code RetriesPerPeriod times at RetryInterval hour intervals (e.g., 9:30am, 11:30am, and 1:30pm) if needed
			time.Sleep(time.Duration(config.RetryInterval)*time.Hour - elapsed)
		}
		// repeat the next day
		time.Sleep(time.Duration(config.Period-(config.RetryInterval*config.RetriesPerPeriod)) * time.Hour)
	}
}

// configure loads config params and BW
func configure() {
	loadConfigFile()
	bw2client = bw2bind.ConnectOrExit("")
	bw2client.OverrideAutoChainTo(true)
	bw2client.SetEntityFromEnvironOrExit()
}

// loadConfigFile loads configuration paramters from config file
func loadConfigFile() {
	notified = false
	f, err := os.Open(confPath)
	if err != nil {
		notify("Error: failed to load configuration file (./config.json). "+err.Error(), config.Devtopic, config.Devtopicregion)
		log.Fatal(errors.New("Error: failed to load configuration file (./config.json). " + err.Error()))
	}
	d := json.NewDecoder(f)
	err = d.Decode(&config)
	if err != nil {
		notify("Error: failed to configure server. "+err.Error(), config.Devtopic, config.Devtopicregion)
		log.Fatal(errors.New("Error: failed to configure server. " + err.Error()))
	}
	if config.Period < config.RetriesPerPeriod*config.RetryInterval {
		notify("Error: Invalid settings, RetriesPerPeriod * RetryInterval > Period", config.Devtopic, config.Devtopicregion)
		log.Fatal(errors.New("Error: Invalid settings, RetriesPerPeriod * RetryInterval > Period"))
	}
}

// parseTable parses Table for CPP events
func parseTable(z *html.Tokenizer) {
	for {
		tt := z.Next()
		switch tt {
		case html.ErrorToken:
			// End of the document, we're done
			return
		case html.StartTagToken:
			t := z.Token()
			if t.Data == "td" {
				for _, a := range t.Attr {
					if a.Val == "rich-table-cell rich-table-cell-first" {
						z.Next()
						t = z.Token()
						if t.Data == "CPP" {
							parseRows(z)
						}
					}
				}
			}
		}
	}
}

// parseRows parses rows from CPP events table and notifies SNS for each row
func parseRows(z *html.Tokenizer) {
	var s []string
	for {
		tt := z.Next()
		switch tt {
		case html.ErrorToken:
			// End of the document, we're done
			if len(s)%4 != 0 {
				notify("Error: values from parsing SCE website has length: "+strconv.Itoa(len(s))+" values: "+strings.Join(s, ","), config.Devtopic, config.Devtopicregion)
				return
			}
			if len(s) > 0 {

				// if one event only and event is today then try again later in case of a consecutive event getting announced later
				if len(s) == 4 && s[0] == time.Now().Format(layout) {
					notified = false
					return
				}
			}
			for i := 0; i < len(s); i += 4 {
				//if event is today skip it
				if s[i] == time.Now().Format(layout) {
					continue
				}
				//if event is tomorrow publish it to BW DR topic for SCE namespace
				start := time.Now()
				evt := time.Date(start.Year(), start.Month(), start.Day()+1, 0, 0, 0, 0, time.Local)
				if s[i] == evt.Format(layout) {
					publishEvent(Event{1, evt.UnixNano(), time.Now().UnixNano()})
				}
				if s[i] == s[i+1] {
					notify("SCE CPP DR Event CONFIRMED for: "+s[i]+" from: "+s[i+2]+" to: "+s[i+3], config.Usrtopic, config.Usrtopicregion)
				} else {
					notify("SCE CPP DR Event CONFIRMED for start date:"+s[i]+" to end date: "+s[i+1]+" from: "+s[i+2]+" to: "+s[i+3], config.Usrtopic, config.Usrtopicregion)
				}
				notified = true
				// sleep briefly to guarantee delivery of notification in order
				time.Sleep(500 * time.Millisecond)
			}
			return
		case html.StartTagToken:
			t := z.Token()
			if t.Data == "td" {
				for _, a := range t.Attr {
					if a.Val == "rich-table-cell " {
						z.Next()
						t = z.Token()
						if t.Data != "span" {
							s = append(s, t.Data)
							// fmt.Println(s)
						}
					}
				}
			}
		}
	}
}

// notify notifies someone when a DR event is about to happen using AWS SNS
func notify(msg string, topic string, region string) {
	log.Println(msg)
	if config.Disablenotification {
		log.Println("notification is disabled")
		return
	}
	sess := session.Must(session.NewSession())
	//region for AWS SNS topics
	svc := sns.New(sess, aws.NewConfig().WithRegion(region))
	params := &sns.PublishInput{
		Message:  aws.String(msg),
		TopicArn: aws.String(topic),
	}
	_, err := svc.Publish(params)
	if err != nil {
		log.Println("failed to send SNS", err)
	}
}

// publishEvent publishes whether an event is confirmed or not on the DR topic for the SCE namespace
func publishEvent(e Event) bool {
	if config.DisableBWPublish {
		return true
	}
	// /sce/confirmed/demand_response/s.confirmed_demand_response/dr/i.xbos.demand_response_confirmed/signal/info
	service := bw2client.RegisterService(config.BWPubtopic, "s.confirmed_demand_response")
	iface := service.RegisterInterface("dr", "i.xbos.demand_response_confirmed")
	po, err := bw2bind.CreateMsgPackPayloadObject(bw2bind.FromDotForm("2.1.1.10"), e)
	if err != nil {
		log.Println("Error: could not serialize object: ", err)
		notify("XBOS PRICE SERVER - Error: could not serialize object, err:"+err.Error(), config.Devtopic, config.Devtopicregion)
		return false
	}
	err = bw2client.Publish(&bw2bind.PublishParams{
		URI:            iface.SignalURI("info"),
		PayloadObjects: []bw2bind.PayloadObject{po},
		Persist:        true,
	})
	if err != nil {
		log.Println("Could not publish object: ", err)
		notify("PG&E PDP - could not publish object, err:"+err.Error(), config.Devtopic, config.Devtopicregion)
		return false
	}
	log.Println("published", e, "to", iface.SignalURI("info"))
	return true
}
