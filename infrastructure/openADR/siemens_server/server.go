package main

/*
 go build -o siemens_server
 ./drserver

 The Siemens server 1) registers with a Siemens server running REST Hooks
 then 2) listens for a price signal (OpenADR format) from the Siemens server.
 Once the signal is recieved, the pricing information is extracted and
 sent to an energy prediction module, 3) the server then waits for energy
 predictions (based on the published prices) to be generated, 4) once the
 predictions are generated, the server forms a JSON encapsulated XML structure
 to send these predictions back to the Siemens server as a POST message
*/

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/xml"
	"errors"
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"os"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/jbowtie/gokogiri"
	gokogirixml "github.com/jbowtie/gokogiri/xml"
	"github.com/jbowtie/gokogiri/xpath"
)

// override the default HTTP client
var httpclient *http.Client

// configuration file path and variable
const confPath = "./config/config.json"

var config Config

var curEvtMod map[string]ModNumber

// Config parameters
type Config struct {
	Logging          bool                //set to true for detailed logging
	Registered       bool                //set to true if this server is already registered with Siemens
	AddCert          bool                //set to true to add the Siemens certificates
	LocalCertFile    string              //location of client certificate
	LocalCertKey     string              //location of client key
	LocalCACertFile  string              //location of server certificate
	SiemensSubServer string              //address of Siemens subscription server
	SiemensPubServer string              //address of Siemens publishing server
	ServerName       string              //name of siemens server
	AuthString       string              //authentication string for Siemens server
	Loc_addr         string              //public address of this server
	Loc_port         int                 //server port
	BuildingTarrif   map[string][]string //Buildings in each tarrif
}

// OpenADR structure for parsing the price signal
type OpenADR struct {
	XMLName  xml.Name   `xml:"oadrPayload"`
	EiEvents []EiEvents `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent"`
}

type ModNumber struct {
	CurrentMod int
	RevisedMod int
}

type EiEvents struct {
	XMLName            xml.Name    `xml:"eiEvent"`
	EventStatus        string      `xml:"eventDescriptor>eventStatus"`
	ModificationNumber int         `xml:"eventDescriptor>modificationNumber"`
	EventID            string      `xml:"eventDescriptor>eventID"`
	StartDate          string      `xml:"eiActivePeriod>properties>dtstart>date-time"` // SIGNAL start date/time
	TotalDuration      string      `xml:"eiActivePeriod>properties>duration>duration"` // SIGNAL duration PT24=24hours etc.
	GroupID            string      `xml:"eiTarget>groupID"`
	TargetBuilding     string      `xml:"eiTarget>resourceID"`
	ItemUnits          string      `xml:"eiEventSignals>eiEventSignal>currencyPerKWh>itemUnits"`
	Intervals          []Intervals `xml:"eiEventSignals>eiEventSignal>intervals>interval"` // Intervals in a given Duration
}

// Interval structure for parsing the price and duration of each interval
type Intervals struct {
	XMLName   xml.Name `xml:"interval"`
	StartDate string   `xml:"dtstart>date-time"` // Interval start time
	Duration  string   `xml:"duration>duration"` // PT1H=1hour, PT5H=5hours, etc.
	Order     int      `xml:"uid>text"`          // Interval order
	Price     float64  `xml:"signalPayload>payloadFloat>value"`
}

// Price structure for sending the price signal to the prediction module
type Price struct {
	Time     int64 // UTC seconds since epoch
	Price    float64
	Currency string
	Duration int64 // in seconds
}

// Siemens JSON structures for PRICE SIGNAL
type SiemensJSON struct {
	Data SiemensJSONFields `json:"data"`
}

type SiemensJSONFields struct {
	Fields SiemensJSONPayload `json:"fields"`
}

type SiemensJSONPayload struct {
	Payload string `json:"payload"`
}

// registerServer register this server with the Siemens REST Hooks server
// registerServer gets called only once unless the target/port for receiving price signal changes
func registerServer(url string) bool {
	resp, err := httpclient.Get(url)
	if err != nil {
		log.Println("Error: failed to GET", err)
		return false
	}
	defer resp.Body.Close()
	if config.Logging {
		log.Println("Response for GET registerServer:", resp)
	}
	if resp.StatusCode != 200 {
		log.Println("Error: GET status code is:", resp.StatusCode)
		return false
	}
	return true
}

// parseJSONBody parses PRICE SIGNAL JSON from Siemens POST request
// returns an XML string with the necessary PRICE SIGNAL information
// follows 'json:"data>fields>payload"' where payload is the XML OpenADR signal
func parseJSONBody(body []byte) ([]byte, error) {
	jsonbody := SiemensJSON{}
	err := json.Unmarshal(body, &jsonbody)
	if err != nil {
		log.Println("Error: Failed to unmarshal JSON")
		return nil, err
	}
	if len(strings.TrimSpace(jsonbody.Data.Fields.Payload)) == 0 {
		return nil, errors.New("Error: JSON payload is empty or does not exist")
	}
	return []byte(strings.Replace(jsonbody.Data.Fields.Payload, "\\\"", "\"", -1)), nil
}

// parseXMLBody parses PRICE SIGNAL XML from Siemens POST request
// returns a Price slice with the necessary PRICE SIGNAL information
func parseXMLBody(body []byte) ([]Price, EiEvents, error) {

	xmlbody := OpenADR{}
	err := xml.Unmarshal(body, &xmlbody)
	if err != nil {
		log.Println("Error: Failed to unmarshal XML")
		return nil, EiEvents{}, err
	}

	ectr := 0
	for _, eiEvent := range xmlbody.EiEvents {
		if eiEvent.EventStatus != "" {
			ectr++
			//if multiple events detected return an error
			if ectr > 1 {
				return nil, EiEvents{}, errors.New("Error: more than one event detected in payload")
			}
			intervalcount := len(eiEvent.Intervals)
			if intervalcount <= 0 {
				return nil, EiEvents{}, errors.New("Error: intervals are empty")
			}
			var prices []Price
			// sort the intervals based on their uid ordering
			sort.Slice(eiEvent.Intervals, func(i, j int) bool {
				return eiEvent.Intervals[i].Order < eiEvent.Intervals[j].Order
			})

			start, err := parseTime(eiEvent.StartDate)
			if err != nil {
				return nil, EiEvents{}, err
			}
			for i, _ := range eiEvent.Intervals {
				st, err := parseTime(eiEvent.Intervals[i].StartDate)
				if err != nil {
					return nil, EiEvents{}, err
				}
				// check total start date and duration start date match
				if st != start {
					log.Println("start", start, "st", st)
					return nil, EiEvents{}, errors.New("Error: interval start date is incorrect")
				}
				d := parseDuration(eiEvent.Intervals[i].Duration)
				prices = append(prices, Price{st.Unix(), eiEvent.Intervals[i].Price, eiEvent.ItemUnits, d})
				start = start.Add(time.Duration(d) * time.Second)
			}
			// Check total duration equals sum of interval durations
			// orig, err := parseTime(eiEvent.StartDate[dt_dur_ind])
			orig, err := parseTime(eiEvent.StartDate)
			if err != nil {
				return nil, EiEvents{}, err
			}
			if start != orig.Add(time.Duration(parseDuration(eiEvent.TotalDuration))*time.Second) {
				return nil, EiEvents{}, errors.New("Error: total duration does not equal some of individual durations")
			}
			if len(prices) != intervalcount {
				return nil, EiEvents{}, errors.New("Error: total number of intervals does not match list of prices")
			}
			return prices, eiEvent, nil
		}
	}
	return nil, EiEvents{}, errors.New("Error: no active period found in eiEvents")
}

// parseTime parses time from string in format (2006-01-02T15:04:05Z)
func parseTime(t string) (time.Time, error) {
	time, err := time.Parse("2006-01-02T15:04:05Z", t)
	if err != nil {
		log.Println("Error: Failed to parse time")
	}
	return time, err
}

// parseDuration parses duration from string (PT1H ... PT24H)
// default is 1H (3600)
func parseDuration(d string) int64 {
	s := strings.TrimPrefix(d, "PT")
	if strings.HasSuffix(d, "H") {
		s = strings.TrimSuffix(s, "H")
		val, err := strconv.Atoi(s) // 1 ... 24 OR Error
		if err == nil {
			return 3600 * int64(val)
		} else {
			return 3600 // default
		}
	} else if strings.HasSuffix(d, "M") {
		s = strings.TrimSuffix(s, "M")
		val, err := strconv.Atoi(s) // 60, 120, 180, ..., 1440 OR Error
		if err == nil {
			return 60 * int64(val)
		} else {
			return 3600 // default
		}
	} else {
		return 3600 //default
	}
}

// createXMLResponse creates an XML response with predictions to send back to Siemens
func createXMLResponse(demands []float64, body []byte, bldgID string, modNumber string) []byte {
	doc, err := gokogiri.ParseXml(body)
	if err != nil {
		log.Println("Error: failed to parse XML body using gokogiri")
		return nil
	}

	defer doc.Free()
	xp := doc.DocXPathCtx()
	for _, ns := range doc.FirstChild().DeclaredNamespaces() {
		xp.RegisterNamespace(ns.Prefix, ns.Uri)
	}

	// set  requestID
	// if !setXMLNode(doc, "/p2012-07:oadrPayload/p2012-07:oadrSignedObject/p2012-07:oadrDistributeEvent/payloads:requestID", "VEN_REQUEST-"+strconv.Itoa(config.ReqID)) {
	// 	log.Println("Error: cannot find requestID in XML: ", err)
	// 	return nil
	// }

	// set SIGNAL NAME
	if !setXMLNode(doc, "/p2012-07:oadrPayload/p2012-07:oadrSignedObject/p2012-07:oadrDistributeEvent/p2012-07:oadrEvent/p2012-07:eiEvent/energyinterop:eiEventSignals/energyinterop:eiEventSignal/energyinterop:signalName", "BID_LOAD") {
		log.Println("Error: cannot find signalName in XML: ", err)
		return nil
	}

	// set SIGNAL TYPE
	if !setXMLNode(doc, "/p2012-07:oadrPayload/p2012-07:oadrSignedObject/p2012-07:oadrDistributeEvent/p2012-07:oadrEvent/p2012-07:eiEvent/energyinterop:eiEventSignals/energyinterop:eiEventSignal/energyinterop:signalType", "setpoint") {
		log.Println("Error: cannot find signalType in XML: ", err)
		return nil
	}

	// set TARGET (BuildingID)
	p := xpath.Compile("/p2012-07:oadrPayload/p2012-07:oadrSignedObject/p2012-07:oadrDistributeEvent/p2012-07:oadrEvent/p2012-07:eiEvent/energyinterop:eiTarget")
	nodes, err := doc.Search(p)
	if err != nil || len(nodes) == 0 {
		log.Println("Error: cannot find eiTarget in XML: ", err)
		return nil
	}
	for _, node := range nodes {
		node.AddChild("<energyinterop:resourceID>" + bldgID + "</energyinterop:resourceID>")
	}

	// set demands
	uidpath := xpath.Compile("/p2012-07:oadrPayload/p2012-07:oadrSignedObject/p2012-07:oadrDistributeEvent/p2012-07:oadrEvent/p2012-07:eiEvent/energyinterop:eiEventSignals/energyinterop:eiEventSignal/energyinterop:intervals/icalendar-stream:interval/energyinterop:uid/icalendar:text")
	var uid int
	uidnodes, err := doc.Search(uidpath)
	if err != nil || len(uidnodes) == 0 {
		log.Println("Error: cannot find uid in XML: ", err)
		return nil
	}
	valpath := xpath.Compile("/p2012-07:oadrPayload/p2012-07:oadrSignedObject/p2012-07:oadrDistributeEvent/p2012-07:oadrEvent/p2012-07:eiEvent/energyinterop:eiEventSignals/energyinterop:eiEventSignal/energyinterop:intervals/icalendar-stream:interval/energyinterop:signalPayload/energyinterop:payloadFloat/energyinterop:value")
	valnodes, err := doc.Search(valpath)
	if err != nil || len(valnodes) == 0 {
		log.Println("Error: cannot find value in XML: ", err)
		return nil
	}
	for i, uidnode := range uidnodes {
		uid, err = strconv.Atoi(uidnode.Content())
		if err != nil {
			log.Println("Error: failed to parse uid in XML:", err)
			return nil
		}
		valnodes[i].SetContent(strconv.FormatFloat(demands[uid], 'f', 1, 64))
	}

	// increment reqID and save it
	// config.ReqID++
	// if !writeConfig() {
	// 	log.Println("Error: failed to save current ReqID to config file")
	// }
	return doc.ToBuffer(nil)
}

// setXMLNode sets one or multiple nodes defined by the path p using the content c in an XmlDocument
func setXMLNode(doc *gokogirixml.XmlDocument, p string, c string) bool {
	x := xpath.Compile(p)
	nodes, err := doc.Search(x)
	if err != nil || len(nodes) == 0 {
		log.Println("Error: cannot find node with given p: ", p, " err:", err)
		return false
	}
	for _, node := range nodes {
		node.SetContent(c)
	}
	return true
}

// XMLtoJSON wraps the XML demand message to a Siemens JSON Format
func XMLtoJSON(x []byte) []byte {
	if x == nil {
		return nil
	}
	return []byte(strings.Replace("{\nXMLMessage : '"+strings.Replace(string(x), "\n", "", -1)+"'\n}", "\"", "\\\"", -1))
}

// sendPOSTRequest sends a POST request to a server and prints response
func sendPOSTRequest(url string, header string, stream []byte) {
	if stream == nil || header == "" {
		log.Println("Error: empty stream or request header")
		return
	}
	if config.Logging {
		log.Println("POST request is: url:", url, " header", header, " stream", string(stream))
	}
	// POST the request
	resp, err := httpclient.Post(url, header, bytes.NewReader(stream))
	if err != nil {
		log.Println("Error: failed to post message to Siemens: ", err)
	}
	defer resp.Body.Close()
	// print the response
	if config.Logging {
		log.Println(resp)
	}
}

func main() {
	// load server configuration
	configure()
	// serve requests
	http.HandleFunc("/", serverRecover(handler))
	go func() {
		err := http.ListenAndServe("0.0.0.0:"+strconv.Itoa(config.Loc_port), nil)
		if err != nil {
			log.Fatal("ListenAndServe: ", err)
		}
	}()

	// register this server with Siemens to recieve price signal
	// only gets called once
	if !config.Registered {
		if !registerServer(config.SiemensSubServer + config.Loc_addr + "&essa=" + base64.StdEncoding.EncodeToString([]byte(config.AuthString))) {
			log.Fatal(errors.New("Error: failed to register with the Siemens server"))
		}
		config.Registered = true
		writeConfig()
	}
	x := make(chan bool)
	<-x
}

// configure loads server configuration file
func configure() {
	f, err := os.Open(confPath)
	if err != nil {
		log.Fatal(errors.New("Error: failed to load configuration file (./config/config.json). " + err.Error()))
		return
	}
	d := json.NewDecoder(f)
	err = d.Decode(&config)
	if err != nil {
		log.Fatal(errors.New("Error: failed to configure server. " + err.Error()))
		return
	}
	addCert()
	curEvtMod = make(map[string]ModNumber)
}

// writeConfig saves current configuration to config file
func writeConfig() bool {
	b, _ := json.MarshalIndent(config, "", "\t")
	b = bytes.Replace(b, []byte("\\u003c"), []byte("<"), -1)
	b = bytes.Replace(b, []byte("\\u003e"), []byte(">"), -1)
	b = bytes.Replace(b, []byte("\\u0026"), []byte("&"), -1)
	err := ioutil.WriteFile(confPath, b, 0600)
	if err != nil {
		log.Println("Error: failed to write config file", err)
		return false
	}
	return true
}

// addCert adds trusted client/server certificates from Siemens
func addCert() {
	if !config.AddCert {
		httpclient = &http.Client{Timeout: 10 * time.Second}
		return
	}

	// Get the SystemCertPool, continue with an empty pool on error
	rootCAs, _ := x509.SystemCertPool()
	if rootCAs == nil {
		rootCAs = x509.NewCertPool()
	}

	// Read in the cert file
	certs, err := ioutil.ReadFile(config.LocalCACertFile)
	if err != nil {
		log.Fatalf("Failed to append %q to RootCAs: %v", config.LocalCertFile, err)
	}

	// Append our cert to the system pool
	if ok := rootCAs.AppendCertsFromPEM(certs); !ok {
		log.Fatal("No certs appended")
	}

	cert, err := tls.LoadX509KeyPair(config.LocalCertFile, config.LocalCertKey)
	if err != nil {
		log.Fatal(err)
	}

	// Trust the augmented cert pool in our client
	config := &tls.Config{
		RootCAs:      rootCAs,
		Certificates: []tls.Certificate{cert},
		ServerName:   config.ServerName,
	}
	config.BuildNameToCertificate()
	tr := &http.Transport{TLSClientConfig: config}
	httpclient = &http.Client{Transport: tr,
		Timeout: 10 * time.Second,
	}
}

// getPredictions gets energy predictions from the prediction module based on the published price signal
// TODO update to use to energy predictions from Thanos's control prediction model
func getPredictions(bldgID string, prices []Price) []float64 {
	predictions := make([]float64, len(prices))
	// currently hardcoded to return a random demand
	rnd := rand.New(rand.NewSource(time.Now().UnixNano()))
	values := []float64{23.5, 16.9, 12.9, 15.2, 20.7}
	for i, _ := range predictions {
		predictions[i] = values[rnd.Intn(5)]
	}
	if config.Logging {
		log.Println("Predictions for building:", bldgID, "are:", predictions)
	}
	return predictions
}

// handler handles POST requests from Siemens server
func handler(w http.ResponseWriter, req *http.Request) {
	// read signal
	defer req.Body.Close()
	body, err := ioutil.ReadAll(req.Body)
	if body == nil || err != nil {
		log.Println("Error: could not read request body or body is empty:", err)
		http.Error(w, "Error: could not read request body or body is empty:"+err.Error(), http.StatusUnsupportedMediaType)
		return
	}
	// log and unpack Seimens formatted JSON message to an XML PRICE SIGNAL
	if config.Logging {
		log.Println("Receieved POST request:", string(body))
	}
	xmlbody, err := parseJSONBody(body)
	if xmlbody == nil || err != nil {
		log.Println("Error: failed to parse JSON price signal, err:", err)
		http.Error(w, "Error: failed to parse JSON price signal, err:"+err.Error(), http.StatusUnsupportedMediaType)
		return
	}
	//log and unpack Siemens formatted XML message to a Price slice and an event
	if config.Logging {
		log.Println("XML Price Signal is: ", string(xmlbody))
	}
	prices, event, err := parseXMLBody(xmlbody)
	if err != nil || prices == nil {
		log.Println("Error: failed to parse XML price signal, err:", err)
		http.Error(w, "Error: failed to parse XML price signal, err:"+err.Error(), http.StatusUnsupportedMediaType)
		return
	}
	if event.GroupID == "" && event.TargetBuilding == "" {
		log.Println("Error: both target groupID and target building are empty")
		http.Error(w, "Error: both target groupID and target building are empty", http.StatusUnsupportedMediaType)
		return
	}

	if event.GroupID != "" {
		_, ok := config.BuildingTarrif[event.GroupID]
		if !ok {
			log.Println("Error: invalid target groupID", event.GroupID)
			http.Error(w, "Error: invalid target groupID", http.StatusUnsupportedMediaType)
			return
		}
	}
	// if signal parsed properly log extracted prices and return OK
	if config.Logging {
		log.Println("Prices are:", prices, "Target GroupID is:", event.GroupID, "Target BuildingID is:", event.TargetBuilding, "EventID", event.EventID, "Modification Number", event.ModificationNumber)
	}
	w.WriteHeader(200)
	w.Write([]byte("OK"))

	// only respond to far events (ignore active or completed events)
	if event.EventStatus == "far" {
		//TODO get and check Modification Number
		modNumber := ""
		if mod, ok := curEvtMod[event.EventID]; ok {
			if mod.CurrentMod == event.ModificationNumber {
				mod.RevisedMod += 10000
				curEvtMod[event.EventID] = ModNumber{event.ModificationNumber, mod.RevisedMod}
				modNumber = strconv.Itoa(mod.RevisedMod)
			} else if mod.CurrentMod < event.ModificationNumber {
				curEvtMod[event.EventID] = ModNumber{event.ModificationNumber, event.ModificationNumber}
				modNumber = strconv.Itoa(event.ModificationNumber)
			} else {
				log.Println("Error: invalid event ModificationNumber")
				return
			}
		} else { //this is the first mod for this event
			curEvtMod[event.EventID] = ModNumber{event.ModificationNumber, event.ModificationNumber}
			modNumber = strconv.Itoa(event.ModificationNumber)
		}
		if config.Logging {
			log.Println("current events and modification", curEvtMod)
		}
		// send energy predictions to Siemens as an XML POST
		if event.TargetBuilding != "" {
			sendPOSTRequest(config.SiemensPubServer, "application/json", XMLtoJSON(createXMLResponse(getPredictions(event.TargetBuilding, prices), xmlbody, event.TargetBuilding, modNumber)))
		} else {
			// if EPRI then don't return predictions (ignore)
			if event.GroupID == "DLAP_PGAE-APND" || event.GroupID == "DLAP_SCE-APND" {
				return
			}
			bldgs, _ := config.BuildingTarrif[event.GroupID]
			for _, bldg := range bldgs {
				sendPOSTRequest(config.SiemensPubServer, "application/json", XMLtoJSON(createXMLResponse(getPredictions(bldg, prices), xmlbody, bldg, modNumber)))
			}
		}
	}
}

// serverRecover recovers from a paniced server
func serverRecover(f func(w http.ResponseWriter, r *http.Request)) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if r := recover(); r != nil {
				log.Println("Panic recovered! err:", r)
				http.Error(w, r.(runtime.Error).Error(), http.StatusInternalServerError)
			}
		}()
		f(w, r)
	}
}
