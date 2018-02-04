package main

/*
 * go build -o drserver
 * ./drserver
 *
 * This is a server that 1) registers with a Siemens server running REST Hooks
 * then 2) listens for a price signal (DR-event) from the Siemens server
 * Once the signal is recieved, the pricing information is extracted and
 * published securely over BOSSWAVE, 3) the server then waits for energy
 * predictions (based on the published prices) to be generated, 4) once the
 * predictions are generated, the server forms an XML structure and sends
 * these predictions back to the Siemens server as a POST message
 */

import (
	"encoding/xml"
	"fmt"
	"log"
	"net/http"
	"time"

	"gopkg.in/immesys/bw2bind.v5"
)

// structure for parsing the incoming PRICE SIGNAL
type OpenADR struct {
	XMLName   xml.Name `xml:"oadrPayload"`
	StartDate string   `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent>eiActivePeriod>properties>dtstart>date-time"`
	Items     []Item   `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent>eiEventSignals>eiEventSignal>intervals>interval"`
}

// structure for parsing interval price
type Item struct {
	XMLName  xml.Name `xml:"interval"`
	Duration string   `xml:"duration>duration"` //PT1H
	Interval int64    `xml:"uid>text"`          //0,1,..., 23
	Price    float64  `xml:"signalPayload>payloadFloat>value"`
}

// structure for sending the price signal over BOSSWAVE
type Price struct {
	Time     int64 // UTC seconds since epoch
	Price    float64
	Unit     string
	Duration int64 // time in seconds
}

// function to parse the time interval extracted from the XML
func parse(s string, d int64) time.Time {
	t, err := time.Parse("2006-01-02T15:04:05Z", s)
	if err != nil {
		panic(err)
	}
	return t.Add(time.Duration(d) * time.Hour)
}

// function to publish the price signal securely over BOSSWAVE
func publishSignal(prices []Price) bool {
	if prices == nil {
		return false
	}
	client := bw2bind.ConnectOrExit("")
	client.OverrideAutoChainTo(true)
	client.SetEntityFromEnvironOrExit()
	service := client.RegisterService("xbos/events/dr", "s.dr")
	iface := service.RegisterInterface("sdb", "i.xbos.dr_signal")
	po, err := bw2bind.CreateMsgPackPayloadObject(bw2bind.FromDotForm("2.9.9.9"), prices)
	if err != nil {
		log.Println("Could not serialize object", err)
		return false
	}
	err = iface.PublishSignal("signal", po)
	if err != nil {
		log.Println("Could not publish object", err)
		return false
	}
	log.Println("Published!")
	return true
}

// function to parse PRICE SIGNAL XML from POST request
// returns a Price array with the necessary PRICE SIGNAL information
func parseXMLBody(req *http.Request) []Price {
	body := OpenADR{}
	xml.NewDecoder(req.Body).Decode(&body)
	defer req.Body.Close()
	var prices []Price
	for i, _ := range body.Items {
		var duration int64
		//TODO add other types of duration that might get passed default is 1H
		switch body.Items[i].Duration {
		case "PT1H":
			duration = 3600
		default:
			duration = 3600
		}
		prices = append(prices, Price{parse(body.StartDate, body.Items[i].Interval).Unix(), body.Items[i].Price, "$", duration})
	}
	return prices
}

// function to register with the Siemens REST Hooks server
// Gets called only once unless the target for receiving price signal changes
func registerServer(url string) bool {
	// send GET request to the Siemens REST Hooks
	resp, err := http.Get(url)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	// make sure response is 200 OK otherwise return false
	fmt.Println(resp)
	if resp.StatusCode != 200 {
		panic(err)
	}
	return true
}

// function to handle POST requests from Siemens server
func handler(w http.ResponseWriter, req *http.Request) {
	prices := parseXMLBody(req)
	if prices != nil {
		w.WriteHeader(200)
		w.Write([]byte("OK"))
	} else {
		w.WriteHeader(400)
		w.Write([]byte("Failed to parse XML price signal"))
	}
	publishSignal(prices)
	// TODO subscribe to energy predictions and send to Siemens as an XML Post
}

func main() {
	loc_addr := "http://localhost"
	loc_port := ":8080"
	if !registerServer("http://epicdr.org:9187/v1/messaging/subscribe?event=PRICE-BAS&target=" + loc_addr + loc_port) {
		panic("Error failed to register with the Siemens server")
	}

	http.HandleFunc("/", handler)
	err := http.ListenAndServe(loc_port, nil)
	if err != nil {
		log.Fatal("ListenAndServe: ", err)
	}
}
