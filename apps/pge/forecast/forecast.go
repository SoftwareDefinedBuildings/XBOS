/*
 go build -o pgeforecast
 ./pgeforecast

 THIS PROGRAM FOLLOWS TO AN EXTENT THE FOLLOWING LOGIC:
 https://www.pge.com/resources/js/pge_five_day_forecast_par-pdp.js

 The program runs once every a predefined hour period and checks the likelihood of
 an event in the next predefined number of days (MAX forecast is 7 days)
 (e.g., runs once every 24 hours and checks the forecast for the next 5 days)

 The program publishes the DR forecast to a DR forecast topic in the PG&E namespace
 If there is a chance an event will occur:
  it uses AWS SNS to notify everyone on the user topic
 If the code fails (in case PG&E changes their logic):
  it will notify everyone on the developer topic
*/

package main

import (
	"encoding/json"
	"errors"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/sns"
	"gopkg.in/immesys/bw2bind.v5"
)

// configuration file path and variable
const confPath = "./config.json"

var config Config

// BOSSWAVE client
var bw2client *bw2bind.BW2Client

type Config struct {
	Logging             bool   //set to true for detailed logging
	Usrtopic            string //AWS user SNS topic
	Usrtopicregion      string //AWS user SNS topic region
	Devtopic            string //AWS developer SNS topic
	Devtopicregion      string //AWS developer SNS topic region
	Disablenotification bool   //set true to disable SNS notification
	DisableBWPublish    bool   //set to true to disable publishing events to BW
	BWPubtopic          string //BOSSWAVE PGE topic (e.g.,pge/confirmed/demand_response/)
	RunOnce             bool   //set to true for run this program once otherwise run every Period
	Period              int    //Overall period in hours to repeat notification (e.g., 24 hours)
	Forecastdays        int    //Number of days to get the forecast for MAX = 7
	Pgeurl              string //URL for PG&E temperature forecast
	WkdyMxTmp           int    //weekday temperature setpoint for a likely event
	WkdyMnTmp           int    //weekday temperature setpoint for a possible event
	WkenMxTmp           int    //weekend temperature setpoint for a likely event
	WkenMnTmp           int    //weekend temperature setpoint for a possible event
}

// Event structure for publishing to the PG&E Forecast DR topic
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
		//GET CSV with temperatures from PG&E
		resp, err := httpclient.Get(config.Pgeurl)
		if err != nil {
			notify("Error: failed to GET temperatures from PG&E: "+err.Error(), config.Devtopic, config.Devtopicregion)
			break Main
		}
		defer resp.Body.Close()
		if config.Logging {
			log.Println("Response for GET registerServer:", resp)
		}
		if resp.StatusCode != 200 {
			notify("Error: GET status code is: "+strconv.Itoa(resp.StatusCode), config.Devtopic, config.Devtopicregion)
			break Main
		}
		body, err := ioutil.ReadAll(resp.Body)
		if body == nil || err != nil {
			notify("Error: could not read request body or body is empty:"+err.Error(), config.Devtopic, config.Devtopicregion)
			break Main
		}
		if config.Logging {
			log.Println("csv is:", string(body))
		}
		log.Println("about to parse CSV file")
		//Parse PG&E CSV
		allTextLines := strings.Split(string(body), "\n")
		if config.Logging {
			log.Println("dates are:", allTextLines[3])
		}
		dateRow := strings.Split(allTextLines[3], ",")
		if config.Logging {
			log.Println("temperatures are:", allTextLines[26])
		}
		tempRow := strings.Split(allTextLines[26], ",")
		var events []Event
		for i := 0; i < 2*config.Forecastdays; i += 2 {
			// parse time
			dt, err := parseTime(dateRow[i+9])
			if err != nil {
				notify("Error: failed to parseTime "+err.Error(), config.Devtopic, config.Devtopicregion)
				break Main
			}
			evt := time.Date(dt.Year(), dt.Month(), dt.Day(), 0, 0, 0, 0, time.Local)

			// parse temperature
			tmp, err := strconv.Atoi(tempRow[i+18])
			if err != nil {
				notify("could not parse temperature:"+tempRow[i+18]+" "+err.Error(), config.Devtopic, config.Devtopicregion)
				break Main
			}
			// if weekend or holiday then threshold temp is 105, otherwise its 98
			if dt.Weekday() == 0 || dt.Weekday() == 6 || isHoliday(dt) {
				if tmp >= config.WkenMxTmp {
					events = append(events, Event{2, evt.UnixNano(), time.Now().UnixNano()})
					notify("PG&E PDP DR event likely to happen on weekend or holiday: "+dateRow[i+9]+" temp: "+tempRow[i+18], config.Usrtopic, config.Usrtopicregion)
				} else if tmp >= config.WkenMnTmp {
					events = append(events, Event{1, evt.UnixNano(), time.Now().UnixNano()})
					log.Println("PG&E PDP DR event possible to happen on weekend or holiday: ", dateRow[i+9], "temp:", tempRow[i+18])
				} else {
					events = append(events, Event{0, evt.UnixNano(), time.Now().UnixNano()})
					log.Println("PG&E PDP DR event unlikely to happen on weekend or holiday:", dateRow[i+9], "temp:", tempRow[i+18])
				}
			} else {
				if tmp >= config.WkdyMxTmp {
					events = append(events, Event{2, evt.UnixNano(), time.Now().UnixNano()})
					notify("PG&E PDP DR event likely to happen on weekday: "+dateRow[i+9]+" temp: "+tempRow[i+18], config.Usrtopic, config.Usrtopicregion)
				} else if tmp >= config.WkdyMnTmp {
					events = append(events, Event{1, evt.UnixNano(), time.Now().UnixNano()})
					log.Println("PG&E PDP DR event possible to happen on weekday:", dateRow[i+9], "temp:", tempRow[i+18])
				} else {
					events = append(events, Event{0, evt.UnixNano(), time.Now().UnixNano()})
					log.Println("PG&E PDP DR event unlikely to happen on weekday:", dateRow[i+9], "temp:", tempRow[i+18])
				}
			}
			// sleep briefly to guarantee delivery of notification in order
			time.Sleep(500 * time.Millisecond)
		}
		publishEvent(events)
		// if configured to run once then break main otherwise sleep
		if config.RunOnce {
			break Main
		}
		// run this code once every Period hours (e.g., 24 hours)
		elapsed := time.Since(start)
		time.Sleep(time.Duration(config.Period)*time.Hour - elapsed)
	}
}

// isHoliday returns true if the given date falls on a PG&E defined holiday for 2018
func isHoliday(t time.Time) bool {
	switch t.Month() {
	case 1: //Jan 1 and 15
		return t.Day() == 1 || t.Day() == 15
	case 2: //Feb 19
		return t.Day() == 19
	case 5: //May 28
		return t.Day() == 28
	case 7: //Jul 4
		return t.Day() == 4
	case 9: //Sep 3
		return t.Day() == 3
	case 11: //Nov 12 and 22
		return t.Day() == 12 || t.Day() == 22
	case 12: //Dec 25
		return t.Day() == 25
	default:
		return false
	}
}

// parseTime parses time from string in format (M/D/YYYY)
func parseTime(t string) (time.Time, error) {
	time, err := time.Parse("1/2/2006", t)
	if err != nil {
		log.Println("Error: Failed to parse time")
	}
	return time, err
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
	}
	d := json.NewDecoder(f)
	err = d.Decode(&config)
	if err != nil {
		notify("Error: failed to configure server. "+err.Error(), config.Devtopic, config.Devtopicregion)
		log.Fatal(errors.New("Error: failed to configure server. " + err.Error()))
	}
	if config.Forecastdays > 7 {
		notify("Error: Forecastdays cannot exceed 7 days, setting to 7", config.Devtopic, config.Devtopicregion)
		log.Println("Forecastdays cannot exceed 7 days, setting to 7")
		config.Forecastdays = 7
	}
}

// publishEvent publishes a DR event forecast for the next N days on the DR topic for the PG&E namespace
func publishEvent(e []Event) bool {
	if config.DisableBWPublish {
		return true
	}
	// /pge/forecast/demand_response/s.forecast_demand_response/dr/i.xbos.demand_response_forecast/signal/info
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
