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
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/jbowtie/gokogiri"
	"github.com/jbowtie/gokogiri/xpath"
	"gopkg.in/immesys/bw2bind.v5"
)

// HTTP Client
var client = &http.Client{Timeout: 10 * time.Second}
var buildingID = "ciee"

// structure for parsing the price/demand signal
type OpenADR struct {
	XMLName       xml.Name    `xml:"oadrPayload"`
	StartDate     string      `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent>eiActivePeriod>properties>dtstart>date-time"` // SIGNAL start date/time
	TotalDuration string      `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent>eiActivePeriod>properties>duration>duration"` // SIGNAL duration PT24=24hours etc.
	Intervals     []Intervals `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent>eiEventSignals>eiEventSignal>intervals>interval"`
}

// structure for parsing interval price/demand
type Intervals struct {
	XMLName  xml.Name `xml:"interval"`
	Duration string   `xml:"duration>duration"` //PT1H=1hour, PT5H=5hours, etc.
	Price    float64  `xml:"signalPayload>payloadFloat>value"`
}

// structure for sending the price signal over BOSSWAVE
type Price struct {
	Time     int64 // UTC seconds since epoch
	Price    float64
	Unit     string
	Duration int64 // time in seconds
}

// function to wrap XML demand message in Siemens JSON Format
func XMLtoJSON(xmlbody []byte) []byte {
	return []byte(strings.Replace("{\nXMLMessage : '"+strings.Replace(string(xmlbody), "\n", "", -1)+"'\n}", "\"", "\\\"", -1))
}

// function to unwrap Seimens formatted JSON message to a proper XML PRICE SIGNAL
func JSONtoXML(jsonbody []byte) []byte {
	return []byte(strings.Replace(strings.Split(string(jsonbody), "'")[1], "\\\"", "\"", -1))
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
	log.Println(resp)
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
	for i, _ := range xmlbody.Intervals {
		var duration int64 // default is 1H (3600 seconds)
		switch xmlbody.Intervals[i].Duration {
		case "PT1H":
			duration = 3600
		case "PT2H":
			duration = 3600 * 2
		case "PT3H":
			duration = 3600 * 3
		case "PT4H":
			duration = 3600 * 4
		case "PT5H":
			duration = 3600 * 5
		case "PT6H":
			duration = 3600 * 6
		case "PT7H":
			duration = 3600 * 7
		case "PT8H":
			duration = 3600 * 8
		case "PT9H":
			duration = 3600 * 9
		case "PT10H":
			duration = 3600 * 10
		case "PT11H":
			duration = 3600 * 11
		case "PT12H":
			duration = 3600 * 12
		case "PT13H":
			duration = 3600 * 13
		case "PT14H":
			duration = 3600 * 14
		case "PT15H":
			duration = 3600 * 15
		case "PT16H":
			duration = 3600 * 16
		case "PT17H":
			duration = 3600 * 17
		case "PT18H":
			duration = 3600 * 18
		case "PT19H":
			duration = 3600 * 19
		case "PT20H":
			duration = 3600 * 20
		case "PT21H":
			duration = 3600 * 21
		case "PT22H":
			duration = 3600 * 22
		case "PT23H":
			duration = 3600 * 23
		case "PT24H":
			duration = 3600 * 24
		default:
			duration = 3600
		}
		prices = append(prices, Price{parse(xmlbody.StartDate, duration).Unix(), xmlbody.Intervals[i].Price, "$", duration})
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
	return []float64{23.5, 16.9, 12.9, 15.2, 20.7}
	// return []float64{22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 45.2, 45.2, 45.2, 62.8, 12.1, 12.1, 12.2, 15.1, 15.1, 34.7, 34.7, 24.3, 24.3, 24.3}
}

// function to create XML response to send back to Siemens
func createXMLResponse(demands []float64, body []byte) []byte {
	doc, _ := gokogiri.ParseXml(body)
	defer doc.Free()
	//TODO read namespace from oadrPayload attributes instead of being hardcoded
	xp := doc.DocXPathCtx()
	xp.RegisterNamespace("xmlns", "http://www.w3.org/2000/09/xmldsig#")
	xp.RegisterNamespace("ns2", "urn:ietf:params:xml:ns:icalendar-2.0")
	xp.RegisterNamespace("ns3", "http://openadr.org/oadr-2.0b/2012/07")
	xp.RegisterNamespace("ns4", "http://docs.oasis-open.org/ns/emix/2011/06/siscale")
	xp.RegisterNamespace("ns5", "http://www.w3.org/2005/Atom")
	xp.RegisterNamespace("ns6", "http://docs.oasis-open.org/ns/emix/2011/06/power")
	xp.RegisterNamespace("ns7", "http://docs.oasis-open.org/ns/energyinterop/201110")
	xp.RegisterNamespace("ns8", "http://www.opengis.net/gml/3.2")
	xp.RegisterNamespace("ns9", "http://docs.oasis-open.org/ns/emix/2011/06")
	xp.RegisterNamespace("ns11", "urn:ietf:params:xml:ns:icalendar-2.0:stream")
	xp.RegisterNamespace("ns12", "http://docs.oasis-open.org/ns/energyinterop/201110/payloads")
	xp.RegisterNamespace("ns13", "http://openadr.org/oadr-2.0b/2012/07/xmldsig-properties")
	xp.RegisterNamespace("ns14", "urn:un:unece:uncefact:codelist:standard:5:ISO42173A:2010-04-07")

	// set first requestID
	x := xpath.Compile("/ns3:oadrPayload/ns3:oadrSignedObject/ns3:oadrDistributeEvent/ns7:eiResponse/ns12:requestID")
	nodes, err := doc.Search(x)
	if err != nil {
		log.Println("cannot find first requestID in XML: ", err)
		return nil
	}
	// TODO better way to set requestID
	// create a random requestID
	src := rand.NewSource(time.Now().UnixNano())
	rnd := rand.New(src)
	reqID := strconv.Itoa(rnd.Intn(10000))
	for _, node := range nodes {
		node.SetContent("VEN_REQUEST-" + reqID)
	}

	// set second requestID
	x = xpath.Compile("/ns3:oadrPayload/ns3:oadrSignedObject/ns3:oadrDistributeEvent/ns12:requestID")
	nodes, err = doc.Search(x)
	if err != nil {
		log.Println("cannot find second requestID in XML: ", err)
		return nil
	}
	for _, node := range nodes {
		node.SetContent("VEN_REQUEST-" + reqID)
	}

	// set SIGNAL NAME
	x = xpath.Compile("/ns3:oadrPayload/ns3:oadrSignedObject/ns3:oadrDistributeEvent/ns3:oadrEvent/ns7:eiEvent/ns7:eiEventSignals/ns7:eiEventSignal/ns7:signalName")
	nodes, err = doc.Search(x)
	if err != nil {
		log.Println("cannot find signalName in XML: ", err)
		return nil
	}
	for _, node := range nodes {
		node.SetContent("BID_LOAD")
	}

	// set SIGNAL TYPE
	x = xpath.Compile("/ns3:oadrPayload/ns3:oadrSignedObject/ns3:oadrDistributeEvent/ns3:oadrEvent/ns7:eiEvent/ns7:eiEventSignals/ns7:eiEventSignal/ns7:signalType")
	nodes, err = doc.Search(x)
	if err != nil {
		log.Println("cannot find signalType in XML: ", err)
		return nil
	}
	for _, node := range nodes {
		node.SetContent("setpoint")
	}

	// set TARGET (BuildingID)
	x = xpath.Compile("/ns3:oadrPayload/ns3:oadrSignedObject/ns3:oadrDistributeEvent/ns3:oadrEvent/ns7:eiEvent/ns7:eiTarget/ns7:resourceID")
	nodes, err = doc.Search(x)
	if err != nil {
		log.Println("cannot find resourceID in XML: ", err)
		return nil
	}
	for _, node := range nodes {
		node.SetContent(buildingID)
	}

	// set demands
	// TODO what is the float format f.d? currently only one decimal
	x = xpath.Compile("/ns3:oadrPayload/ns3:oadrSignedObject/ns3:oadrDistributeEvent/ns3:oadrEvent/ns7:eiEvent/ns7:eiEventSignals/ns7:eiEventSignal/ns11:intervals/ns7:interval/ns7:signalPayload/ns7:payloadFloat/ns7:value")
	nodes, err = doc.Search(x)
	if err != nil {
		log.Println("cannot find value in XML: ", err)
		return nil
	}
	for i, node := range nodes {
		node.SetContent(strconv.FormatFloat(demands[i], 'f', 1, 64))
	}
	return doc.ToBuffer(nil)
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
	log.Println(resp)
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
	// unpack JSON to XML
	body = JSONtoXML(body)
	if body == nil {
		log.Println("Could not parse JSON price signal body")
		http.Error(w, "Could not parse JSON price signal body", http.StatusUnsupportedMediaType)
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
		log.Println("Failed to parse XML price signal")
		http.Error(w, "Failed to parse XML price signal", http.StatusUnsupportedMediaType)
		return
	}
	// publish prices securely over BOSSWAVE
	publishSignal(prices)

	// TODO subscribe to energy predictions and send to Siemens as an XML POST
	// FOR NOW WE WILL SEND BACK A HARD CODED SIGNAL BUT WILL REPLACE IN THE
	// FUTURE WITH DYNAMIC/ACCURATE PREDICTIONS
	sendPOSTRequest("http://epicdr.org:9187/v1/messaging/publish/DEMAND-BAS", "application/json", XMLtoJSON(createXMLResponse(getPredictions(), body)))
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
