package main

/*
 go build -o siemens_server
 ./siemens_server

 This server 1) registers with a Siemens server running REST Hooks
 2) listens for a price signal (in a slightly modified OpenADR format).
 3) Once the signal is recieved from the Siemens server, the pricing information
 and target building or tariff is extracted.
 4) For each building or group of buildings that fall under the given tariff,
 the prices along with the building ID are sent to an energy prediction module
 5) The external energy prediction module generates a demand forecast based on
 given price
 6) Once the predictions are generated, the server creates a JSON encapsulated
 XML structure (in the same format as the received price signal)
 7) The server sends these predictions back to the Siemens server as a POST message
*/

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/xml"
	"errors"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"time"

	"google.golang.org/grpc"

	"github.com/jbowtie/gokogiri"
	gokogirixml "github.com/jbowtie/gokogiri/xml"
	"github.com/jbowtie/gokogiri/xpath"
)

// configuration file path and variable
const confPath = "./config/config.json"

var config Config

// gRPC params
// var conn *grpc.ClientConn
// var stub DemandForecastClient

// BuildingMapping TODO: update empty
var BuildingMapping = map[string]string{
	"LBNL":  "",
	"AAS":   "avenal-animal-shelter",
	"AVH":   "avenal-veterans-hall",
	"ARC":   "avenal-recreation-center",
	"APWD":  "avenal-public-works-yard",
	"SBSC":  "south-berkeley-senior-center",
	"CIEE":  "ciee",
	"WFCC":  "word-of-faith-cc",
	"HFS8":  "hayward-station-8",
	"BC":    "",
	"OCC":   "orinda-community-center",
	"OL":    "orinda-public-library",
	"HFS1":  "hayward-station-1",
	"NBSC":  "north-berkeley-senior-center",
	"BCY":   "berkeley-corporation-yard",
	"LBS":   "local-butcher-shop",
	"AMT":   "avenal-movie-theatre",
	"RFS":   "rfs",
	"GSH":   "",
	"SDH":   "",
	"CSUDH": "csu-dominguez-hills",
	"JTFCC": "jesse-turner-center",
}

// Config parameters
type Config struct {
	Logging              bool                //set to true for detailed logging
	Registered           bool                //set to true if this server is already registered with Siemens
	IgnoreEpri           bool                //set to true to ignore EPRI signal (consume but don't return predictions)
	ClientTimeout        int                 //timeout in seconds for a http client
	AddCert              bool                //set to true to add the Siemens certificates
	LocalCertFile        string              //location of client certificate
	LocalCertKey         string              //location of client key
	LocalCACertFile      string              //location of server certificate
	SiemensSubServer     string              //address of Siemens subscription server
	SiemensPubServer     string              //address of Siemens publishing server
	ServerName           string              //name of siemens server
	AuthString           string              //authentication string for Siemens server
	LocalAddress         string              //public address of this server
	LocalPort            int                 //server port
	DemandForecastServer string              //address and port of demand forecast grpc server
	BuildingTarrif       map[string][]string //Buildings in each tarrif
}

// server internal state variables
var curEvtMod map[string]ModNumber //map of current input/output modificationNumber for an eventID-GroupID

// ModNumber structure to keep the current input/output modificationNumber
type ModNumber struct {
	CurrentMod int //the current input modificationNumber
	RevisedMod int //the current output modificationNumber
}

// OpenADR structure for parsing the price signal
type OpenADR struct {
	XMLName   xml.Name   `xml:"oadrPayload"`
	RequestID string     `xml:"oadrSignedObject>oadrDistributeEvent>requestID"`
	EiEvents  []EiEvents `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent"`
}

// EiEvents structure for parsing the events in a price signal
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

// Intervals structure for parsing the price and duration of each interval
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

// SiemensJSON structures for PRICE SIGNAL
type SiemensJSON struct {
	Data SiemensJSONFields `json:"data"`
}

// SiemensJSONFields structure for PRICE SIGNAL
type SiemensJSONFields struct {
	Fields SiemensJSONPayload `json:"fields"`
}

// SiemensJSONPayload structure for PRICE SIGNAL
type SiemensJSONPayload struct {
	Payload string `json:"payload"`
}

func main() {
	// load server configuration
	configure()
	// init server state
	curEvtMod = make(map[string]ModNumber)
	// register this server with Siemens to recieve price signal
	// only gets called once unless the port or local address changes
	if !config.Registered {
		if !registerServer(config.SiemensSubServer + config.LocalAddress + "&essa=" + base64.StdEncoding.EncodeToString([]byte(config.AuthString))) {
			log.Fatal(errors.New("Error: failed to register with the Siemens server"))
		}
		config.Registered = true
		//save the state of registeration
		writeConfig()
	}

	// serve requests
	http.HandleFunc("/", serverRecover(handler))
	go func() {
		err := http.ListenAndServe(":"+strconv.Itoa(config.LocalPort), nil)
		if err != nil {
			log.Fatal("ListenAndServe: ", err)
		}
	}()

	x := make(chan bool)
	<-x
}

// configure loads server configuration from config file
func configure() {
	f, err := os.Open(confPath)
	if err != nil {
		log.Fatal(errors.New("Error: failed to load configuration file (./config/config.json). " + err.Error()))
	}
	d := json.NewDecoder(f)
	err = d.Decode(&config)
	if err != nil {
		log.Fatal(errors.New("Error: failed to configure server. " + err.Error()))
	}
}

// writeConfig saves current server configuration to config file
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

// registerServer register this server with the Siemens REST Hooks server
// registerServer gets called only once unless the target/port for receiving price signal changes
func registerServer(url string) bool {
	httpclient := getHTTPClient()
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

// getHTTPClient overrides the default HTTP client and adds trusted client/server certificates from Siemens
func getHTTPClient() *http.Client {
	if !config.AddCert {
		return &http.Client{Timeout: time.Duration(config.ClientTimeout) * time.Second}
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
	conf := &tls.Config{
		RootCAs:      rootCAs,
		Certificates: []tls.Certificate{cert},
		ServerName:   config.ServerName,
	}
	conf.BuildNameToCertificate()
	tr := &http.Transport{TLSClientConfig: conf}
	return &http.Client{Transport: tr,
		Timeout: time.Duration(config.ClientTimeout) * time.Second,
	}
}

// handler handles incoming POST requests from Siemens server
func handler(w http.ResponseWriter, req *http.Request) {
	log.Println(req.Header)
	// read signal
	body, err := ioutil.ReadAll(req.Body)
	if body == nil || err != nil {
		log.Println("Error: could not read request body or body is empty:", err)
		http.Error(w, "Error: could not read request body or body is empty:"+err.Error(), http.StatusUnsupportedMediaType)
		return
	}

	//TODO remove this if unnecessary
	err = ioutil.WriteFile("requests/"+strconv.Itoa(time.Now().Nanosecond())+".json", body, 0600)
	if err != nil {
		log.Println("Error: failed to write incoming POST request to file", err)
		http.Error(w, "Error: failed to write incoming POST request to file, err: "+err.Error(), http.StatusUnsupportedMediaType)
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
	//log and unpack Siemens formatted XML message to a Price slice , requestID, and an event
	if config.Logging {
		log.Println("XML Price Signal is: ", string(xmlbody))
	}
	prices, reqID, event, err := parseXMLBody(xmlbody)
	// if failed to parseXMLBody return an error to Siemens
	if err != nil || prices == nil {
		log.Println("Error: failed to parse XML price signal, err:", err)
		http.Error(w, "Error: failed to parse XML price signal, err:"+err.Error(), http.StatusUnsupportedMediaType)
		return
	}
	// if the signal doesn't have a tariff or a buildingID return an error to Siemens
	if event.GroupID == "" && event.TargetBuilding == "" {
		log.Println("Error: both target groupID and target building are empty")
		http.Error(w, "Error: both target groupID and target building are empty", http.StatusUnsupportedMediaType)
		return
	}
	// if the target tariff is invalid return an error to Siemens to Siemens
	if event.GroupID != "" {
		_, ok := config.BuildingTarrif[event.GroupID]
		if !ok {
			log.Println("Error: invalid target groupID", event.GroupID)
			http.Error(w, "Error: invalid target groupID", http.StatusUnsupportedMediaType)
			return
		}
	}
	// if signal parsed properly log extracted prices and return OK
	log.Println("Prices are:", prices, "Target GroupID is:", event.GroupID, "Target BuildingID is:", event.TargetBuilding, "EventID", event.EventID, "Modification Number", event.ModificationNumber)
	w.WriteHeader(200)
	w.Write([]byte("OK"))
	go replyToSiemens(event, prices, reqID, xmlbody)
}

func replyToSiemens(event EiEvents, prices []Price, reqID string, xmlbody []byte) {
	// only respond to far events (ignore active or completed events)
	if event.EventStatus == "far" {
		//setup grpc connection (one per request)
		var opts []grpc.DialOption
		opts = append(opts,
			grpc.WithBlock(),
			grpc.FailOnNonTempDialError(true),
			grpc.WithInsecure(),
		)
		conn, err := grpc.Dial(config.DemandForecastServer, opts...)
		if err != nil {
			log.Println(errors.New("Error: failed to connect to DemandForecastServer on: " + config.DemandForecastServer + ". Error: " + err.Error()))
			return
		}
		defer conn.Close()
		stub := NewDemandForecastClient(conn)

		//create an output modificationNumber based on the current state and input modificationNumber
		modNumber := ""
		key := event.EventID + event.GroupID
		if mod, ok := curEvtMod[key]; ok {
			if mod.CurrentMod == event.ModificationNumber {
				mod.RevisedMod += 10000
				curEvtMod[key] = ModNumber{event.ModificationNumber, mod.RevisedMod}
				modNumber = strconv.Itoa(mod.RevisedMod)
			} else if mod.CurrentMod < event.ModificationNumber {
				curEvtMod[key] = ModNumber{event.ModificationNumber, event.ModificationNumber}
				modNumber = strconv.Itoa(event.ModificationNumber)
			} else {
				log.Println("Error: invalid event ModificationNumber")
				return
			}
		} else { //this is the first modificationNumber for this event
			curEvtMod[key] = ModNumber{event.ModificationNumber, event.ModificationNumber}
			modNumber = strconv.Itoa(event.ModificationNumber)
		}

		if len(prices) == 0 {
			return
		}

		if config.Logging {
			log.Println("current events and modification", curEvtMod)
		}
		// Contact the server and print out its response.

		// send energy predictions to Siemens as an XML POST
		if event.TargetBuilding != "" {
			str := strconv.Itoa(1) + " for eventID: " + "VEN_REQUEST-" + event.TargetBuilding + "-" + reqID + "-" + modNumber + " modificationNumber: " + modNumber + " resourceID: " + event.TargetBuilding
			sendPOSTRequest(str, config.SiemensPubServer, "application/json", XMLtoJSON(createXMLResponse(getPredictions(stub, event.TargetBuilding, prices), xmlbody, event.TargetBuilding, modNumber, reqID)))
		} else {
			// Ignore EPRI GROUP signal if the server configuration is set true (don't return predictions)
			if config.IgnoreEpri {
				if event.GroupID == "DLAP_PGAE-APND" || event.GroupID == "DLAP_SCE-APND" {
					return
				}
			}
			// send energy predictions for each building in the groupID (tariff)
			bldgs, _ := config.BuildingTarrif[event.GroupID]
			for i, bldg := range bldgs {
				str := strconv.Itoa(i+1) + " for groupID: " + event.GroupID + " eventID: " + "VEN_REQUEST-" + bldg + "-" + reqID + "-" + modNumber + " modificationNumber: " + modNumber + " resourceID: " + bldg
				sendPOSTRequest(str, config.SiemensPubServer, "application/json", XMLtoJSON(createXMLResponse(getPredictions(stub, bldg, prices), xmlbody, bldg, modNumber, reqID)))
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
// returns a Price slice with the necessary PRICE SIGNAL information, a requestID, and event information
func parseXMLBody(body []byte) ([]Price, string, EiEvents, error) {
	xmlbody := OpenADR{}
	err := xml.Unmarshal(body, &xmlbody)
	if err != nil {
		log.Println("Error: Failed to unmarshal XML")
		return nil, "", EiEvents{}, err
	}
	ectr := 0
	for _, eiEvent := range xmlbody.EiEvents {
		if eiEvent.EventStatus != "" {
			ectr++
			//if multiple events detected return an error
			if ectr > 1 {
				return nil, "", EiEvents{}, errors.New("Error: more than one event detected in payload")
			}
			intervalcount := len(eiEvent.Intervals)
			if intervalcount <= 0 {
				return nil, "", EiEvents{}, errors.New("Error: intervals are empty")
			}
			var prices []Price
			// sort the intervals based on their uid ordering
			sort.Slice(eiEvent.Intervals, func(i, j int) bool {
				return eiEvent.Intervals[i].Order < eiEvent.Intervals[j].Order
			})

			start, err := parseTime(eiEvent.StartDate)
			if err != nil {
				return nil, "", EiEvents{}, err
			}
			for i := range eiEvent.Intervals {
				st, e := parseTime(eiEvent.Intervals[i].StartDate)
				if e != nil {
					return nil, "", EiEvents{}, e
				}
				// check total start date and duration start date match
				if st != start {
					log.Println("start", start, "st", st)
					return nil, "", EiEvents{}, errors.New("Error: interval start date is incorrect")
				}
				d := parseDuration(eiEvent.Intervals[i].Duration)
				prices = append(prices, Price{st.UnixNano(), eiEvent.Intervals[i].Price, eiEvent.ItemUnits, d})
				start = start.Add(time.Duration(d) * time.Second)
			}
			// Check total duration equals sum of interval durations
			// orig, err := parseTime(eiEvent.StartDate[dt_dur_ind])
			orig, err := parseTime(eiEvent.StartDate)
			if err != nil {
				return nil, "", EiEvents{}, err
			}
			if start != orig.Add(time.Duration(parseDuration(eiEvent.TotalDuration))*time.Second) {
				return nil, "", EiEvents{}, errors.New("Error: total duration does not equal some of individual durations")
			}
			if len(prices) != intervalcount {
				return nil, "", EiEvents{}, errors.New("Error: total number of intervals does not match list of prices")
			}
			return prices, xmlbody.RequestID, eiEvent, nil
		}
	}
	return nil, "", EiEvents{}, errors.New("Error: no active period found in eiEvents")
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
		}
	} else if strings.HasSuffix(d, "M") {
		s = strings.TrimSuffix(s, "M")
		val, err := strconv.Atoi(s) // 60, 120, 180, ..., 1440 OR Error
		if err == nil {
			return 60 * int64(val)
		}
	}
	return 3600 //default
}

// getPredictions gets energy predictions from the prediction module based on the published price signal for a given building
func getPredictions(stub DemandForecastClient, bldgID string, prices []Price) []float64 {
	predictions := make([]float64, len(prices))
	pricepoints := make([]*PricePoint, len(prices))
	log.Println("getting predictions for: ", bldgID, " start time: ", time.Unix(0, prices[0].Time).String(), " end time: ", time.Unix(0, prices[len(prices)-1].Time).String())
	for i, price := range prices {
		pricepoints[i] = &PricePoint{Time: price.Time, Duration: strconv.FormatInt(price.Duration, 10) + "s", Price: price.Price, Unit: price.Currency}
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	r, err := stub.GetDemandForecast(ctx, &DemandForecastRequest{Building: BuildingMapping[bldgID], Start: prices[0].Time, End: prices[len(prices)-1].Time + prices[len(prices)-1].Duration*1e9, Prices: pricepoints})
	if err != nil {
		log.Printf("could not get price: %v", err.Error())
		return nil
	}
	if len(r.Demands) == len(predictions) {
		for i, demand := range r.Demands {
			predictions[i] = demand.Demand
		}
	}

	log.Println("Predictions for building:", bldgID, "are:", predictions)
	return predictions
}

// createXMLResponse creates an XML response with predictions to send back to Siemens
func createXMLResponse(demands []float64, body []byte, bldgID string, modNumber string, reqID string) []byte {
	if demands == nil {
		return nil
	}
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
	if !setXMLNode(doc, "/p2012-07:oadrPayload/p2012-07:oadrSignedObject/p2012-07:oadrDistributeEvent/payloads:requestID", "VEN_REQUEST-"+bldgID+"-"+reqID+"-"+modNumber) {
		log.Println("Error: cannot find requestID in XML: ", err)
		return nil
	}

	// set ModificationNumber
	if !setXMLNode(doc, "/p2012-07:oadrPayload/p2012-07:oadrSignedObject/p2012-07:oadrDistributeEvent/p2012-07:oadrEvent/p2012-07:eiEvent/energyinterop:eventDescriptor/energyinterop:modificationNumber", modNumber) {
		log.Println("Error: cannot find modificationNumber in XML: ", err)
		return nil
	}

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
func sendPOSTRequest(cntr string, url string, header string, stream []byte) {
	if stream == nil || header == "" {
		log.Println("Error: empty stream or request header")
		return
	}
	if config.Logging {
		log.Println("POST request is: url:", url, " header", header, " stream", string(stream))
	}
	// POST the request
	st := time.Now()
	httpclient := getHTTPClient()
	resp, err := httpclient.Post(url, header, bytes.NewReader(stream))
	if err != nil {
		log.Println("Error: failed to post message to Siemens: ", err)
		log.Println("Post", cntr, " failed after:", time.Since(st))
		return
	}
	defer resp.Body.Close()
	// print the response
	if config.Logging {
		log.Println(resp)
		log.Println("Post", cntr, " took:", time.Since(st))
	}
}
