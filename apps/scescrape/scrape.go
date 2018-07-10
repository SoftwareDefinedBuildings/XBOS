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
					if a.Val == "rich-table EvtTable" {
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
						if t.Data == "CPP" {
							parseRows(z)
						}
					}
				}
			}
		}
	}
}
func parseRows(z *html.Tokenizer) {
	var s []string
	for {
		tt := z.Next()
		switch tt {
		case html.ErrorToken:
			// End of the document, we're done
			if len(s)%4 != 0 {
				notify("Error: values from parsing SCE website has length: "+strconv.Itoa(len(s))+" values: "+strings.Join(s, ","), config.Devtopic)
				return
			}
			for i := 0; i < len(s); i += 4 {
				if s[i] == s[i+1] {
					notify("SCE CPP event scheduled on: "+s[i]+" from: "+s[i+2]+" to: "+s[i+3], config.Usrtopic)
				} else {
					notify("SCE CPP event scheduled for start date:"+s[i]+" end date: "+s[i+1]+" from: "+s[i+2]+" to: "+s[i+3], config.Usrtopic)
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
