/*
 go build -o estimate
 ./estimate
 THIS CODE FOLLOWS TO AN EXTENT THE FOLLOWING LOGIC:
 https://www.pge.com/resources/js/pge_five_day_forecast_par-pdp.js
 The code runs once a day and checks the likelyhood of an event for the next 7 days
 If there is a chance an event will occur it uses AWS SNS to notify someone
 If the code fails (in case PG&E changes their logic), it will notify the developer topic (currently Moustafa)
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
)

// configuration file path and variable
var confPath = "./config.json"
var config Config

type Config struct {
	Usrtopic  string
	Smstopic  string
	Devtopic  string
	Pgeurl    string
	WkdyMxTmp int
	WkdyMnTmp int
	WkenMxTmp int
	WkenMnTmp int
}

func main() {
	configure()
	httpclient := &http.Client{Timeout: 10 * time.Second}
Main:
	for {
		//GET CSV with temperatures from PG&E
		resp, err := httpclient.Get(config.Pgeurl)
		if err != nil {
			notify("Error: failed to GET temperatures from PG&E: "+err.Error(), []string{config.Devtopic})
			break Main
		}
		defer resp.Body.Close()
		log.Println("Response for GET registerServer:", resp)
		if resp.StatusCode != 200 {
			notify("Error: GET status code is: "+strconv.Itoa(resp.StatusCode), []string{config.Devtopic})
			break Main
		}
		body, err := ioutil.ReadAll(resp.Body)
		if body == nil || err != nil {
			notify("Error: could not read request body or body is empty:"+err.Error(), []string{config.Devtopic})
			break Main
		}
		log.Println("csv is:", string(body))
		//Parse PG&E CSV
		allTextLines := strings.Split(string(body), "\n")
		log.Println("dates are:", allTextLines[3])
		dateRow := strings.Split(allTextLines[3], ",")
		log.Println("temperatures are:", allTextLines[26])
		tempRow := strings.Split(allTextLines[26], ",")

		for i := 0; i < 14; i += 2 {
			// parse time
			dt, err := parseTime(dateRow[i+9])
			if err != nil {
				notify("Error: failed to parseTime "+err.Error(), []string{config.Devtopic})
				break Main
			}
			// parse temperature
			tmp, err := strconv.Atoi(tempRow[i+18])
			if err != nil {
				notify("could not parse temperature:"+tempRow[i+18]+" "+err.Error(), []string{config.Devtopic})
				break Main
			}
			// if weekend or holiday then threshold temp is 105, otherwise its 98
			if dt.Weekday() == 0 || dt.Weekday() == 6 || isHoliday(dt) {
				if tmp >= config.WkenMxTmp {
					notify("PG&E PDP DR event likely to happen on weekend or holiday: "+dateRow[i+9]+" temp: "+tempRow[i+18], []string{config.Usrtopic, config.Smstopic})
				} else if tmp >= config.WkenMnTmp {
					log.Println("PG&E PDP DR event possible to happen on weekend or holiday: ", dateRow[i+9], "temp:", tempRow[i+18])
				} else {
					log.Println("PG&E PDP DR event unlikely to happen on weekend or holiday:", dateRow[i+9], "temp:", tempRow[i+18])
				}
			} else {
				if tmp >= config.WkdyMxTmp {
					notify("PG&E PDP DR event likely to happen on weekday: "+dateRow[i+9]+" temp: "+tempRow[i+18], []string{config.Usrtopic, config.Smstopic})
				} else if tmp >= config.WkdyMnTmp {
					log.Println("PG&E PDP DR event possible to happen on weekday:", dateRow[i+9], "temp:", tempRow[i+18])
				} else {
					log.Println("PG&E PDP DR event unlikely to happen on weekday:", dateRow[i+9], "temp:", tempRow[i+18])
				}
			}
			// sleep briefly to guarantee delivery of notification in order
			time.Sleep(500 * time.Millisecond)
		}
		// run this code once a day
		time.Sleep(24 * time.Hour)
		// reload configuration in case threshold temperatures changed
		configure()
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
func notify(msg string, topics []string) {
	log.Println(msg)
	sess := session.Must(session.NewSession())
	for _, topic := range topics {
		//region for AWS SNS topics
		svc := sns.New(sess, aws.NewConfig().WithRegion("us-west-1"))
		if topic == config.Smstopic {
			//region for SMS
			svc = sns.New(sess, aws.NewConfig().WithRegion("us-west-2"))
		}

		params := &sns.PublishInput{
			Message:  aws.String(msg),
			TopicArn: aws.String(topic),
		}
		_, err := svc.Publish(params)

		if err != nil {
			log.Println("failed to send SNS", err)
		}
	}
}

// configure loads configuration paramters from config file
func configure() {
	f, err := os.Open(confPath)
	if err != nil {
		log.Fatal(errors.New("Error: failed to load configuration file (./config.json). " + err.Error()))
		return
	}
	d := json.NewDecoder(f)
	err = d.Decode(&config)
	if err != nil {
		log.Fatal(errors.New("Error: failed to configure server. " + err.Error()))
		return
	}
}
