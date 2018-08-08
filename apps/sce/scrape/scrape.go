/*
 go build -o sceconfirmed
 ./sceconfirmed

 The code runs a predefined times separated by predefined hours during a predefined period
 (e.g., run 3 times every 2 hours in 24 hours)

 The code checks for a confirmed SCE CPP event by scraping SCE's website

 If there is an event:
     it uses AWS SNS to notify everyone on the user topic
 If the is an error (e.g., error parsing):
     it will notify everyone on the developer topic
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
)

// configuration file path and variable
const confPath = "./config.json"

var config Config
var notified bool

type Config struct {
	Usrtopic            string //AWS user SNS topic
	Usrtopicregion      string //AWS user SNS topic region
	Devtopic            string //AWS developer SNS topic
	Devtopicregion      string //AWS developer SNS topic region
	Disablenotification bool   //set true to disable SNS notification
	Sceurl              string //URL for SCE CPP website
	Period              int    //Overall period in hours to repeat notification (e.g., 24 hours)
	RetriesPerPeriod    int    //Max number of retries per period
	RetryInterval       int    //Wait time in hours between retries
}

func main() {
	httpclient := &http.Client{Timeout: 10 * time.Second}
Main:
	for {
		// reload configuration in case something changed
		configure()
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
			// run this code RetriesPerPeriod times at RetryInterval hour intervals (e.g., 9:30am, 11:30am, and 1:30pm) if needed
			time.Sleep(time.Duration(config.RetryInterval)*time.Hour - elapsed)
		}
		// repeat the next day
		time.Sleep(time.Duration(config.Period-(config.RetryInterval*config.RetriesPerPeriod)) * time.Hour)
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
				// if event is today then try again later in case of a consecutive event getting announced later
				if s[0] != time.Now().Format("02/01/2006") {
					notified = true
				}
			}
			for i := 0; i < len(s); i += 4 {
				if s[i] == s[i+1] {
					notify("SCE CPP DR Event CONFIRMED for: "+s[i]+" from: "+s[i+2]+" to: "+s[i+3], config.Usrtopic, config.Usrtopicregion)
				} else {
					notify("SCE CPP DR Event CONFIRMED for start date:"+s[i]+" to end date: "+s[i+1]+" from: "+s[i+2]+" to: "+s[i+3], config.Usrtopic, config.Usrtopicregion)
				}
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

// configure loads configuration paramters from config file
func configure() {
	f, err := os.Open(confPath)
	if err != nil {
		log.Fatal(errors.New("Error: failed to load configuration file (./config.json). " + err.Error()))
	}
	d := json.NewDecoder(f)
	err = d.Decode(&config)
	if err != nil {
		log.Fatal(errors.New("Error: failed to configure server. " + err.Error()))
	}
	if config.Period < config.RetriesPerPeriod*config.RetryInterval {
		log.Fatal(errors.New("Error: Invalid settings, RetriesPerPeriod * RetryInterval > Period"))
	}
	notified = false
}
