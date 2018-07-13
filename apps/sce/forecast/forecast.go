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
)

// configuration file path and variable
var confPath = "./config.json"
var config Config

type Config struct {
	Usrtopic string
	Devtopic string
	Sceurl   string
}

func main() {
	configure()
	// request and parse the front page
	httpclient := &http.Client{Timeout: 10 * time.Second}

Main:
	for {
		resp, err := httpclient.Get(config.Sceurl)
		if err != nil {
			notify("Error: failed to GET main website from SCE: "+err.Error(), config.Devtopic)
			break Main
		}
		defer resp.Body.Close()
		if resp.StatusCode != 200 {
			notify("Error: GET status code is: "+strconv.Itoa(resp.StatusCode), config.Devtopic)
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
					if a.Val == "rich-table EvtRTPTable" {
						parseTable(z)
					}
				}
			}
		}
		// run this code once a day
		time.Sleep(24 * time.Hour)
		// reload configuration in case something changed
		configure()
	}
}
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
						if parseDate(t.Data) {
							s := parseRows(z)
							log.Println(t.Data, s)
							//see for more details on CPP https://www.sce.com/NR/sc3/tm2/pdf/ce300.pdf
							if s == "EXTREMELY HOT SUMMER WEEKDAY" {
								notify("SCE CPP DR event likely to happen on: "+t.Data+" from: 2:00 pm to 6:00 pm", config.Usrtopic)
							}
						}
					}
				}
			}
		}
	}
}
func parseDate(t string) bool {
	//July 16, 2018
	// _, err := time.Parse("2006-01-02T15:04:05Z", t)
	_, err := time.Parse("January 02, 2006", t)
	if err != nil {
		return false
	}
	return true

}
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
func notify(msg string, topic string) {
	log.Println(msg)
	sess := session.Must(session.NewSession())

	//region for AWS SNS topics
	svc := sns.New(sess, aws.NewConfig().WithRegion("us-west-2"))
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
		return
	}
	d := json.NewDecoder(f)
	err = d.Decode(&config)
	if err != nil {
		log.Fatal(errors.New("Error: failed to configure server. " + err.Error()))
		return
	}
}
