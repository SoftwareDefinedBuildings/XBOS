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
	"bytes"
	"encoding/xml"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/jbowtie/gokogiri"
	"github.com/jbowtie/gokogiri/xpath"
	"gopkg.in/immesys/bw2bind.v5"
)

// HTTP Client
var client = &http.Client{Timeout: 10 * time.Second}

// structure for parsing the price/demand signal
type OpenADR struct {
	XMLName    xml.Name `xml:"oadrPayload"`
	StartDate  string   `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent>eiActivePeriod>properties>dtstart>date-time"` // SIGNAL start date/time
	SignalName string   `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent>eiEventSignals>eiEventSignal>signalName"`     // BID_LOAD or ELECTRICITY_PRICE
	SignalType string   `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent>eiEventSignals>eiEventSignal>signalType"`     // setpoint or price
	Target     string   `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent>eiTarget"`                                    // building ID
	Items      []Item   `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent>eiEventSignals>eiEventSignal>intervals>interval"`
}

// structure for parsing interval price/demand
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

// function to register with the Siemens REST Hooks server
// Gets called only once unless the target for receiving price signal changes
func registerServer(url string) bool {
	// send GET request to the Siemens REST Hooks
	resp, err := client.Get(url)
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

// function to parse PRICE SIGNAL XML from Siemens POST request
// returns a Price array with the necessary PRICE SIGNAL information
func parseXMLBody(body []byte) []Price {
	xmlbody := OpenADR{}
	xml.Unmarshal(body, &xmlbody)
	var prices []Price
	for i, _ := range xmlbody.Items {
		var duration int64 // seconds
		//TODO add other types of duration that might get passed default is 1H
		switch xmlbody.Items[i].Duration {
		case "PT1H":
			duration = 3600
		default:
			duration = 3600
		}
		prices = append(prices, Price{parse(xmlbody.StartDate, xmlbody.Items[i].Interval*duration).Unix(), xmlbody.Items[i].Price, "$", duration})
	}
	return prices
}

// function to parse the time interval extracted from the XML
func parse(s string, d int64) time.Time {
	t, err := time.Parse("2006-01-02T15:04:05Z", s)
	if err != nil {
		panic(err)
	}
	return t.Add(time.Duration(d) * time.Second)
}

// function to recover from a paniced func parse or parseXMLBody
func parseRecover(w http.ResponseWriter) {
	if r := recover(); r != nil {
		log.Println("Failed to parse XML price signal: ", r)
		http.Error(w, r.(string), http.StatusInternalServerError)
	}
}

// function to publish the price signal securely over BOSSWAVE
// TODO Modify this function to publish to individual buildings or add building ID
func publishSignal(prices []Price) bool {
	client := bw2bind.ConnectOrExit("")
	client.OverrideAutoChainTo(true)
	client.SetEntityFromEnvironOrExit()
	service := client.RegisterService("xbos/events/dr", "s.dr")
	iface := service.RegisterInterface("sdb", "i.xbos.dr_signal")
	po, err := bw2bind.CreateMsgPackPayloadObject(bw2bind.FromDotForm("2.9.9.9"), prices)
	if err != nil {
		log.Println("Could not serialize object: ", err)
		return false
	}
	err = iface.PublishSignal("signal", po)
	if err != nil {
		log.Println("Could not publish object: ", err)
		return false
	}
	log.Println("Published!")
	return true
}

// function to get predictions (eventually over BOSSWAVE)
// TODO currently hardcoded update to contact Thanos's control
func getPredictions() []float64 {
	return []float64{22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 45.2, 45.2, 45.2, 62.8, 12.1, 12.1, 12.2, 15.1, 15.1, 34.7, 34.7, 24.3, 24.3, 24.3}
}

// function to create XML response to send back to Siemens
func createXMLResponse(demands []float64, body []byte) []byte {
	doc, _ := gokogiri.ParseXml(body)
	defer doc.Free()
	//TODO read namespace from oadrPayload attributes instead of being hardcoded
	xp := doc.DocXPathCtx()
	xp.RegisterNamespace("emix", "http://docs.oasis-open.org/ns/emix/2011/06")
	xp.RegisterNamespace("power", "http://docs.oasis-open.org/ns/emix/2011/06/power")
	xp.RegisterNamespace("scale", "http://docs.oasis-open.org/ns/emix/2011/06/siscale")
	xp.RegisterNamespace("ei", "http://docs.oasis-open.org/ns/energyinterop/201110")
	xp.RegisterNamespace("pyld", "http://docs.oasis-open.org/ns/energyinterop/201110/payloads")
	xp.RegisterNamespace("oadr", "http://openadr.org/oadr-2.0b/2012/07")
	xp.RegisterNamespace("n2", "http://www.altova.com/samplexml/other-namespace")
	xp.RegisterNamespace("gml", "http://www.opengis.net/gml/3.2")
	xp.RegisterNamespace("ds", "http://www.w3.org/2000/09/xmldsig#")
	xp.RegisterNamespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
	xp.RegisterNamespace("atom", "http://www.w3.org/2005/Atom")
	xp.RegisterNamespace("xcal", "urn:ietf:params:xml:ns:icalendar-2.0")
	xp.RegisterNamespace("strm", "urn:ietf:params:xml:ns:icalendar-2.0:stream")

	// set SIGNAL NAME
	x := xpath.Compile("/oadr:oadrPayload/oadr:oadrSignedObject/oadr:oadrDistributeEvent/oadr:oadrEvent/ei:eiEvent/ei:eiEventSignals/ei:eiEventSignal/ei:signalName")
	nodes, err := doc.Search(x)
	if err != nil {
		log.Println("cannot find signalName in XML: ", err)
		return nil
	}
	for _, node := range nodes {
		node.SetContent("BID_LOAD")
	}

	// set SIGNAL TYPE
	x = xpath.Compile("/oadr:oadrPayload/oadr:oadrSignedObject/oadr:oadrDistributeEvent/oadr:oadrEvent/ei:eiEvent/ei:eiEventSignals/ei:eiEventSignal/ei:signalType")
	nodes, err = doc.Search(x)
	if err != nil {
		log.Println("cannot find signalType in XML: ", err)
		return nil
	}
	for _, node := range nodes {
		node.SetContent("setpoint")
	}

	// set TARGET
	x = xpath.Compile("/oadr:oadrPayload/oadr:oadrSignedObject/oadr:oadrDistributeEvent/oadr:oadrEvent/ei:eiEvent/ei:eiTarget")
	nodes, err = doc.Search(x)
	if err != nil {
		log.Println("cannot find eiTarget in XML: ", err)
		return nil
	}
	// TODO set target using buildingID
	// for i, node := range nodes {
	// node.SetContent("buildingID")
	// }

	// set demands
	// TODO what is the float format f.d? currently only one decimal
	x = xpath.Compile("/oadr:oadrPayload/oadr:oadrSignedObject/oadr:oadrDistributeEvent/oadr:oadrEvent/ei:eiEvent/ei:eiEventSignals/ei:eiEventSignal/strm:intervals/ei:interval/ei:signalPayload/ei:payloadFloat/ei:value")
	nodes, err = doc.Search(x)
	if err != nil {
		log.Println("cannot find value in XML: ", err)
		return nil
	}
	for i, node := range nodes {
		node.SetContent(strconv.FormatFloat(demands[i], 'f', 1, 64))
	}
	ret, _ := doc.ToXml(nil, nil)
	return ret
}

// function to send a POST request to a server
func sendPOSTRequest(url string, header string, stream []byte) {
	if stream == nil || header == "" {
		log.Fatal("Error empty stream or request header")
		return
	}

	// POST the request
	resp, err := client.Post(url, header, bytes.NewReader(stream))
	if err != nil {
		log.Fatal("Failed to post message to Siemens: ", err)
	}
	defer resp.Body.Close()

	// print the response
	fmt.Println(resp)
}

// function to handle POST requests from Siemens server
func handler(w http.ResponseWriter, req *http.Request) {
	// read signal
	defer req.Body.Close()
	body, err := ioutil.ReadAll(req.Body)
	if err != nil {
		log.Println("Could not read request body: ", err)
		http.Error(w, err.Error(), http.StatusUnsupportedMediaType)
		return
	}
	// parse signal to extract prices
	defer parseRecover(w)
	prices := parseXMLBody(body)
	// if signal parsed properly return OK
	if prices != nil {
		w.WriteHeader(200)
		w.Write([]byte("OK"))
	} else {
		log.Println("Failed to parse XML price signal: ", err)
		http.Error(w, err.Error(), http.StatusUnsupportedMediaType)
		return
	}
	// publish prices securely over BOSSWAVE
	publishSignal(prices)

	// TODO subscribe to energy predictions and send to Siemens as an XML POST
	// FOR NOW WE WILL SEND BACK A HARD CODED SIGNAL BUT WILL REPLACE IN THE
	// FUTURE WITH DYNAMIC/ACCURATE PREDICTIONS
	sendPOSTRequest("http://epicdr.org:9187/v1/messaging/publish/DEMAND-BAS", "text/xml", createXMLResponse(getPredictions(), body))
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
