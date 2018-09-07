/*
 go build -o sceforecast
 ./sceforecast

 The program runs once every a predefined hour period and checks the likelihood of
 an event in the next predefined number of days (MAX forecast is 5 days)
 (e.g., runs once every 24 hours and checks the forecast for the next 5 days)

 for more details on CPP visit https://www.sce.com/NR/sc3/tm2/pdf/ce300.pdf

 The program publishes the DR forecast to a DR forecast topic in the SCE namespace
 If there is a chance an event will occur:
  it uses AWS SNS to notify everyone on the user topic
 If the code fails (in case SCE changes their website):
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

// BOSSWAVE client
var bw2client *bw2bind.BW2Client

// time format for notification
const layout = "January 02, 2006"

type Config struct {
	Usrtopic            string //AWS user SNS topic
	Usrtopicregion      string //AWS user SNS topic region
	Devtopic            string //AWS developer SNS topic
	Devtopicregion      string //AWS developer SNS topic region
	Disablenotification bool   //set true to disable SNS notification
	DisableBWPublish    bool   //set to true to disable publishing events to BW
	BWPubtopic          string //BOSSWAVE PGE topic (e.g.,pge/confirmed/demand_response/)
	RunOnce             bool   //set to true for run this program once otherwise run every Period
	Period              int    //Overall period in hours to repeat notification (e.g., 24 hours)
	Forecastdays        int    //Number of days to get the forecast for MAX = 6
	Sceurl              string //URL for SCE  forecast
}

// Event structure for publishing to the SCE Forecast DR topic
type Event struct {
	Event_likelihood int64
	Date             int64
	Time             int64
}

func main() {
	httpclient := &http.Client{Timeout: 10 * time.Second}
	configure()
Main:
	for {
		//reload config file in case settings changed
		loadConfigFile()
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

		log.Println("about to parse website")
		z := html.NewTokenizer(resp.Body)
	ParseTable:
		for {
			tt := z.Next()
			switch tt {
			case html.ErrorToken:
				// End of the document, we're done
				break ParseTable
			case html.StartTagToken:
				t := z.Token()
				for _, a := range t.Attr {
					if a.Val == "rich-table EvtRTPTable" {
						parseTable(z)
					}
				}
			}
		}
		// if configured to run once then break main otherwise sleep
		if config.RunOnce {
			break Main
		}
		// run this code once every Period hours (e.g., 24 hours)
		elapsed := time.Since(start)
		time.Sleep(time.Duration(config.Period)*time.Hour - elapsed)
	}
}

// parseTable parses Table for weather events and notifies SNS for each EXTREMELY HOT SUMMER WEEKDAY row
func parseTable(z *html.Tokenizer) {
	var daycount int
	var events []Event
	for {
		tt := z.Next()
		switch tt {
		case html.ErrorToken:
			// End of the document, we're done
			if len(events) > 0 {
				publishEvent(events)
			}
			return
		case html.StartTagToken:
			t := z.Token()
			if t.Data == "td" {
			ParseRow:
				for _, a := range t.Attr {
					if a.Val == "rich-table-cell rich-table-cell-first" {
						z.Next()
						t = z.Token()
						dt, ok := parseDate(t.Data)

						if ok {
							//skip today's forecast
							if t.Data == time.Now().Format(layout) {
								continue ParseRow
							}
							evt := time.Date(dt.Year(), dt.Month(), dt.Day(), 0, 0, 0, 0, time.Local)
							daycount++
							if daycount > config.Forecastdays {
								break ParseRow
							}
							s := parseRows(z)
							log.Println(t.Data, s)
							if s == "EXTREMELY HOT SUMMER WEEKDAY" {
								events = append(events, Event{2, evt.UnixNano(), time.Now().UnixNano()})
								notify("SCE CPP DR Event likely to happen on: "+t.Data+" from: 2:00 pm to 6:00 pm", config.Usrtopic, config.Usrtopicregion)
							} else if s == "HOT SUMMER WEEKDAY" || s == "VERY HOT SUMMER WEEKDAY" {
								events = append(events, Event{1, evt.UnixNano(), time.Now().UnixNano()})
							} else {
								events = append(events, Event{0, evt.UnixNano(), time.Now().UnixNano()})
							}
						}
					}
				}
			}
		}
	}
}

// parseDate in the format July 16, 2018
func parseDate(t string) (time.Time, bool) {
	dt, err := time.Parse(layout, t)
	if err != nil {
		return dt, false
	}
	return dt, true
}

// parseRows parses rows from temperature table and returns forecast
func parseRows(z *html.Tokenizer) string {
	for {
		tt := z.Next()
		switch tt {
		case html.ErrorToken:
			// End of the document, we're done
			return ""
		case html.StartTagToken:
			t := z.Token()
			if t.Data == "td" {
				for _, a := range t.Attr {
					if a.Val == "rich-table-cell rich-table-cell-last" {
						z.Next()
						t = z.Token()
						return t.Data
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

// configure loads config params and BW
func configure() {
	loadConfigFile()
	bw2client = bw2bind.ConnectOrExit("")
	bw2client.OverrideAutoChainTo(true)
	bw2client.SetEntityFromEnvironOrExit()
}

// loadConfigFile loads configuration paramters from config file
func loadConfigFile() {
	f, err := os.Open(confPath)
	if err != nil {
		notify("Error: failed to load configuration file (./config.json). "+err.Error(), config.Devtopic, config.Devtopicregion)
		log.Fatal(errors.New("Error: failed to load configuration file (./config.json). " + err.Error()))
		return
	}
	d := json.NewDecoder(f)
	err = d.Decode(&config)
	if err != nil {
		notify("Error: failed to configure server. "+err.Error(), config.Devtopic, config.Devtopicregion)
		log.Fatal(errors.New("Error: failed to configure server. " + err.Error()))
		return
	}
	if config.Forecastdays > 5 {
		notify("Error: Forecastdays cannot exceed 5 days, setting to 5", config.Devtopic, config.Devtopicregion)
		log.Println("Forecastdays cannot exceed 5 days, setting to 5")
		config.Forecastdays = 5
	}

}

// publishEvent publishes a DR event forecast for the next N days on the DR topic for the PG&E namespace
func publishEvent(e []Event) bool {
	if config.DisableBWPublish {
		log.Println("publishing", e)
		return true
	}
	// /sce/forecast/demand_response/s.forecast_demand_response/dr/i.xbos.demand_response_forecast/signal/info
	service := bw2client.RegisterService(config.BWPubtopic, "s.forecast_demand_response")
	iface := service.RegisterInterface("dr", "i.xbos.demand_response_forecast")
	po, err := bw2bind.CreateMsgPackPayloadObject(bw2bind.FromDotForm("2.1.1.11"), e)
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
