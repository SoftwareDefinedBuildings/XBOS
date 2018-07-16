/*
 go build -o pgeconfirmed
 ./pgeconfirmed

 The code runs a predefined times separated by predefined hours during a predefined period
 (e.g., run 3 times every 2 hours in 24 hours)

 The code checks for a confirmed PG&E PDP event by subscribing to
 a DR topic on a preconfigured Pelican thermostat

 If there is an event:
     it uses AWS SNS to notify everyone on the user topic
 If the subscription times out a predefined amount of times:
     it will notify everyone on the developer topic
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
	bw2 "gopkg.in/immesys/bw2bind.v5"
)

// configuration file path and variable
const confPath = "./config.json"

var config Config

// BOSSWAVE client
var bw2client *bw2.BW2Client
var msgchan chan *bw2.SimpleMessage

// time format for notification
const layout = "January 02, 2006 at 3:04 PM"

type Config struct {
	Usrtopic            string //AWS user SNS topic
	Usrtopicregion      string //AWS user SNS topic region
	Devtopic            string //AWS developer SNS topic
	Devtopicregion      string //AWS developer SNS topic region
	Disablenotification bool   //set true to disable SNS notification
	BWtopic             string //BOSSWAVE DR topic (e.g., ciee/devices/pelican/s.pelican/+/i.xbos.demand_response/signal/info)
	BTtopicmaxwait      int    //Max wait time in seconds for a message on a topic
	BTtopictimeoutcount int    //Max number of consecutive timeouts before notifying developer
	Period              int    //Overall period in hours to repeat notification (e.g., 24 hours)
	RetriesPerPeriod    int    //Max number of retries per period
	RetryInterval       int    //Wait time in hours between retries
}

type Signal struct {
	Event_start int64 `msgpack:"event_start"`
	Event_end   int64 `msgpack:"event_end"`
	Event_type  int64 `msgpack:"event_type"`
	Dr_status   int64 `msgpack:"dr_status"`
	Time        int64 `msgpack:"time"`
}

func main() {
	var timeoutcount int
Main:
	for {
		// reload configuration in case something changed
		configure()
		for i := 0; i < config.RetriesPerPeriod; i++ {
			start := time.Now()
			// set a timeout for listening on a BW topic
			timer := make(chan string)
			go func() {
				time.Sleep(time.Duration(config.BTtopicmaxwait) * time.Second)
				timer <- ""
			}()
			var dt string
			select {
			case dt = <-timer:
				timeoutcount++
				log.Println("Reading on BWTopic", config.BWtopic, "timed out", timeoutcount, "consecutive time(s)")
				if timeoutcount >= config.BTtopictimeoutcount {
					notify("PG&E PDP - reading on BWTopic "+config.BWtopic+" timed out "+strconv.Itoa(timeoutcount)+" consecutive time(s)", config.Devtopic, config.Devtopicregion)
					//reset timeoutcount and parse message
					timeoutcount = 0
				}
			case msg := <-msgchan:
				//reset timeoutcount and parse message
				timeoutcount = 0
				dt = parseMsg(msg)
			}
			elapsed := time.Since(start)
			//dt is empty if there are no events otherwise dt has start date for the event
			if dt != "" {
				notify("PG&E PDP DR event CONFIRMED for: "+dt, config.Usrtopic, config.Usrtopicregion)
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

// parseMsg reads a message from a BW topic and returns the start date of the DR event
// The start date is 0 if there is no event and a unix time stamp of the event in nanoseconds otherwise
func parseMsg(msg *bw2.SimpleMessage) string {
	log.Println("about to parse BW message")
	var st string
	var sig Signal
	po := msg.GetOnePODF("2.1.1.9")
	if po == nil {
		return st
	}
	err := po.(bw2.MsgPackPayloadObject).ValueInto(&sig)
	if err != nil {
		log.Println(err)
		return st
	} else {
		if sig.Event_start == 0 {
			return st
		} else {
			loc, err := time.LoadLocation("America/Los_Angeles")
			if err != nil {
				return st
			}
			return time.Unix(0, sig.Event_start).In(loc).Format(layout)
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

// configure loads configuration paramters from config file and starts listening on the specified BW topic
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
	bw2client = bw2.ConnectOrExit("")
	bw2client.OverrideAutoChainTo(true)
	bw2client.SetEntityFromEnvironOrExit()
	msgchan, err = bw2client.Subscribe(&bw2.SubscribeParams{URI: config.BWtopic})
	if err != nil {
		log.Fatal(err)
	}
}
