/*
 go build -o pgeconfirmed
 ./pgeconfirmed

 This program runs periodically & checks for a confirmed PG&E PDP event
 by subscribing to a DR topic on a preconfigured Pelican thermostat
 		The pelican thermostat receives the DR signal directly from PG&E

 In the case of an event, the program uses AWS SNS to notify
 		everyone on the AWS PG&E user topic

 If the BW subscription times out a predefined amount of times:
 		it will notify everyone on the developer topic that it can't
		subscribe to the Pelican topic

This program also publishes a message to a BW topic in the PGE namespace
	following the i.xbos.demand_response_confirmed interface

This program can be configured to run once during a predefined period
	(e.g., once every 24 hours)
This program can also be configured to retry multiple times during that period
	This is useful in case the signal is pushed later in the day or if the DR topic is temporarily unavailable
	(e.g., try 3 times (once every 2 hours) during a 24 hour period)

*/

package main

import (
	"encoding/json"
	"errors"
	"log"
	"os"
	"strconv"
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
var msgchan chan *bw2bind.SimpleMessage

// time format for notification
const layout = "January 02, 2006 at 3:04 PM"

type Config struct {
	Usrtopic            string //AWS user SNS topic
	Usrtopicregion      string //AWS user SNS topic region
	Devtopic            string //AWS developer SNS topic
	Devtopicregion      string //AWS developer SNS topic region
	Disablenotification bool   //set true to disable SNS notification
	DisableBWPublish    bool   //set to true to disable publishing events to BW
	BWSubtopic          string //BOSSWAVE DR topic (e.g., ciee/devices/pelican/s.pelican/+/i.xbos.demand_response/signal/info)
	BWPubtopic          string //BOSSWAVE PGE topic (e.g.,pge/confirmed/demand_response/)
	BTtopicmaxwait      int    //Max wait time in seconds for a message on a topic
	BTtopictimeoutcount int    //Max number of consecutive timeouts before notifying developer
	StartTime           string //Start time for this program in HH:MM format
	Period              int    //Overall period in hours to repeat notification (e.g., 24 hours)
	RetriesPerPeriod    int    //Max number of retries per period minimum is 1
	RetryInterval       int    //Wait time in hours between retries
}

// Signal structure for subscribing to the Pelican Thermostat topic
type Signal struct {
	Event_start int64 `msgpack:"event_start"`
	Event_end   int64 `msgpack:"event_end"`
	Event_type  int64 `msgpack:"event_type"`
	Dr_status   int64 `msgpack:"dr_status"`
	Time        int64 `msgpack:"time"`
}

// Event structure for publishing to the PG&E Confirmed DR topic
type Event struct {
	Event_status int64
	Date         int64
	Time         int64
}

func main() {
	var timeoutcount int
	configure()
	// start this program at the start time
	ct, err := time.Parse("15:04", config.StartTime)
	if err != nil {
		notify("Error: failed to parse config.StartTime. "+err.Error(), config.Devtopic, config.Devtopicregion)
		log.Fatal(errors.New("Error: failed to parse config.StartTime. " + err.Error()))
	}
	ct = time.Date(0, 0, 0, ct.Hour(), ct.Minute(), 0, 0, time.Local)
	pt := time.Date(0, 0, 0, time.Now().Hour(), time.Now().Minute(), 0, 0, time.Local)
	if pt.Before(ct) {
		log.Println("sleeping for:", ct.Sub(pt))
		time.Sleep(ct.Sub(pt))
	} else if pt.After(ct) {
		log.Println("sleeping for:", (time.Duration(config.Period)*time.Hour)-pt.Sub(ct))
		time.Sleep((time.Duration(config.Period) * time.Hour) - pt.Sub(ct))
	}
Main:
	for {
		//reload config file in case settings changed
		loadConfigFile()
		for i := 0; i < config.RetriesPerPeriod; i++ {
			start := time.Now()
			// set a timeout for listening on a BW topic
			timer := make(chan string)
			go func() {
				time.Sleep(time.Duration(config.BTtopicmaxwait) * time.Second)
				timer <- ""
			}()
			var dt string
			var dtnano int64
			select {
			case dt = <-timer:
				timeoutcount++
				log.Println("Reading on BWTopic", config.BWSubtopic, "timed out", timeoutcount, "consecutive time(s)")
				if timeoutcount >= config.BTtopictimeoutcount {
					notify("PG&E PDP - reading on BWTopic "+config.BWSubtopic+" timed out "+strconv.Itoa(timeoutcount)+" consecutive time(s)", config.Devtopic, config.Devtopicregion)
					//reset timeoutcount and parse message
					timeoutcount = 0
				}
			case msg := <-msgchan:
				//reset timeoutcount and parse message
				timeoutcount = 0
				dt, dtnano = parseMsg(msg)
			}
			elapsed := time.Since(start)
			//dt is 0 if there are no events, empty if parsing the message caused an error or if subscribtion timed out, otherwise dt is the start date/time for the event
			if dt != "" && dt != "0" {
				//if dt is today ignore
				t := time.Unix(0, dtnano)
				evt := time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, time.Local)
				if time.Date(start.Year(), start.Month(), start.Day(), 0, 0, 0, 0, time.Local) != evt {
					notify("PG&E PDP DR event CONFIRMED for: "+dt, config.Usrtopic, config.Usrtopicregion)
					publishEvent(Event{1, evt.UnixNano(), time.Now().UnixNano()})
					// repeat the next day
					time.Sleep(time.Duration(config.Period-(i*config.RetryInterval))*time.Hour - elapsed)
					continue Main
				}
			} else if dt == "0" {
				// nothing is confirmed for tomorrow publish no event and try again later
				evt := time.Date(start.Year(), start.Month(), start.Day()+1, 0, 0, 0, 0, time.Local)
				publishEvent(Event{0, evt.UnixNano(), time.Now().UnixNano()})
			}

			// run this code RetriesPerPeriod times at RetryInterval hour intervals (e.g., 9:30am, 11:30am, and 1:30pm) if needed
			time.Sleep(time.Duration(config.RetryInterval)*time.Hour - elapsed)

		}
		// repeat the next day
		time.Sleep(time.Duration(config.Period-(config.RetryInterval*config.RetriesPerPeriod)) * time.Hour)
	}
}

// configure loads config params and BW
func configure() {
	bw2client = bw2bind.ConnectOrExit("")
	bw2client.OverrideAutoChainTo(true)
	bw2client.SetEntityFromEnvironOrExit()
	loadConfigFile()
}

// loadConfigFile loads configuration paramters from config file and starts listening on the specified BW topic
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
	if config.Period < config.RetriesPerPeriod*config.RetryInterval {
		notify("Error: Invalid settings, RetriesPerPeriod * RetryInterval > Period", config.Devtopic, config.Devtopicregion)
		log.Fatal(errors.New("Error: Invalid settings, RetriesPerPeriod * RetryInterval > Period"))
	}
	msgchan, err = bw2client.Subscribe(&bw2bind.SubscribeParams{URI: config.BWSubtopic})
	if err != nil {
		notify("Error: failed to subscribe to topic. "+err.Error(), config.Devtopic, config.Devtopicregion)
		log.Fatal(err)
	}
}

// parseMsg reads a message from a BW topic and returns the start date of the DR event
// The start date is 0 if there is no event and a unix time stamp of the event in nanoseconds otherwise
func parseMsg(msg *bw2bind.SimpleMessage) (string, int64) {
	log.Println("about to parse BW message")
	var st string
	var sig Signal
	po := msg.GetOnePODF("2.1.1.9")
	if po == nil {
		return st, 0
	}
	err := po.(bw2bind.MsgPackPayloadObject).ValueInto(&sig)
	if err != nil {
		log.Println(err)
		return st, 0
	} else {
		log.Println("parsed signal", sig)
		if sig.Event_start == 0 {
			return "0", sig.Event_start
		} else {
			loc, err := time.LoadLocation("America/Los_Angeles")
			if err != nil {
				return st, 0
			}
			return time.Unix(0, sig.Event_start).In(loc).Format(layout), sig.Event_start
		}
	}
}

// notify notifies someone when a DR event is about to happen using AWS SNS and notifies developer in case of failure
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

// publishEvent publishes whether an event is confirmed or not on the DR topic for the PGE namespace
func publishEvent(e Event) bool {
	if config.DisableBWPublish {
		return true
	}
	// /pge/confirmed/demand_response/s.confirmed_demand_response/dr/i.xbos.demand_response_confirmed/signal/info
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
