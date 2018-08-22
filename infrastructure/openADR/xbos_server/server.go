/*
 go build -o xbos_price_server
 ./xbos_price_server

 This server 1) listens for a price signal (in an OpenADR format).
 2) Once the signal is recieved, the pricing information for
 a target tariff is extracted.
 3) The pricing information are published to the corresponding utility topic
*/

package main

import (
	"encoding/json"
	"encoding/xml"
	"errors"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strconv"
	"strings"
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

// Config parameters
type Config struct {
	Logging             bool   //set to true for detailed logging
	SaveXML             bool   //set to true to save the incoming price signal to a file
	XMLDir              string //path to dir where XML signals will be stored
	Loc_port            int    //server port
	DisableNotification bool   //set to true to notify developer
	DisableBW           bool   //set to true to disable publishing to BW
	Devtopic            string //AWS developer SNS topic
	Devtopicregion      string //AWS developer SNS topic region
}

// OpenADR structure for parsing the price signal
type OpenADR struct {
	XMLName  xml.Name   `xml:"oadrPayload"`
	EiEvents []EiEvents `xml:"oadrSignedObject>oadrDistributeEvent>oadrEvent>eiEvent"`
}

// EiEvents structure for parsing the events in a price signal
type EiEvents struct {
	XMLName            xml.Name       `xml:"eiEvent"`
	EventID            string         `xml:"eventDescriptor>eventID"`                         // ID of incoming event
	ModificationNumber int            `xml:"eventDescriptor>modificationNumber"`              // modification to an existing event
	EventStatus        string         `xml:"eventDescriptor>eventStatus"`                     // far (future), active (current), complete (past)
	GroupID            string         `xml:"eiTarget>groupID"`                                // tariff
	StartDate          string         `xml:"eiActivePeriod>properties>dtstart>date-time"`     // start date/time for entire event
	TotalDuration      string         `xml:"eiActivePeriod>properties>duration>duration"`     // duration for entire event (PT24=24hours, etc.)
	SignalName         string         `xml:"eiEventSignals>eiEventSignal>signalName"`         // ENERGY_PRICE or DEMAND_PRICE
	CurrencyPerKWh     CurrencyPerKWh `xml:"eiEventSignals>eiEventSignal>currencyPerKWh"`     // currency for energy
	CurrencyPerKW      CurrencyPerKW  `xml:"eiEventSignals>eiEventSignal>currencyPerKW"`      // currency for demand
	Intervals          []Intervals    `xml:"eiEventSignals>eiEventSignal>intervals>interval"` // Intervals in a given Duration
}

// CurrencyPerKWh structure for parsing energy price currency
type CurrencyPerKWh struct {
	XMLName   xml.Name `xml:"currencyPerKWh"`
	ItemUnits string   `xml:"itemUnits"`
}

// CurrencyPerKW structure for parsing demand price currency
type CurrencyPerKW struct {
	XMLName   xml.Name `xml:"currencyPerKW"`
	ItemUnits string   `xml:"itemUnits"`
}

// Interval structure for parsing the price and duration of each interval
type Intervals struct {
	XMLName   xml.Name `xml:"interval"`
	StartDate string   `xml:"dtstart>date-time"`                // Interval start time
	Duration  string   `xml:"duration>duration"`                // PT1H=1hour, PT5H=5hours, etc.
	Order     int      `xml:"uid>text"`                         // Interval order
	Price     float64  `xml:"signalPayload>payloadFloat>value"` // Price for interval
}

// Price structure for sending the price signal to the a given topic
type Price struct {
	StartTime int64 // UTC seconds since epoch
	Duration  int64 // in seconds
	Price     float64
	Currency  int
	Time      int64 // UTC seconds since epoch
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

	x := make(chan bool)
	<-x
}

// configure loads server configuration from config file
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
	}
	if !config.DisableBW {
		bw2client = bw2bind.ConnectOrExit("")
		bw2client.OverrideAutoChainTo(true)
		bw2client.SetEntityFromEnvironOrExit()
	}
}

// handler handles incoming POST requests from Pricing server
func handler(w http.ResponseWriter, req *http.Request) {
	// read signal
	defer req.Body.Close()
	xmlbody, err := ioutil.ReadAll(req.Body)
	if xmlbody == nil || err != nil {
		log.Println("Error: could not read request body or body is empty:", err)
		http.Error(w, "Error: could not read request body or body is empty:"+err.Error(), http.StatusBadRequest)
		notify("XBOS PRICE SERVER - Error: could not read request body or body is empty: "+err.Error(), config.Devtopic, config.Devtopicregion)
		return
	}
	// log XML PRICE SIGNAL
	if config.Logging {
		log.Println("Receieved POST request with XML Price Signal:", string(xmlbody))
	}

	prices, event, err := parseXMLBody(xmlbody)
	// if failed to parseXMLBody return an error to Pricing
	if err != nil || prices == nil {
		log.Println("Error: failed to parse XML price signal, err:", err)
		http.Error(w, "Error: failed to parse XML price signal, err:"+err.Error(), http.StatusBadRequest)
		notify("XBOS PRICE SERVER - Error: failed to parse XML price signal, err:"+err.Error(), config.Devtopic, config.Devtopicregion)
		return
	}
	// if the signal doesn't have a tariff or a buildingID return an error to Pricing Server
	if event.GroupID == "" {
		log.Println("Error: target groupID is empty")
		http.Error(w, "Error: target groupID is empty", http.StatusBadRequest)
		notify("XBOS PRICE SERVER - Error: target groupID is empty", config.Devtopic, config.Devtopicregion)
		return
	}
	// write XML to file
	if config.SaveXML {
		dir := filepath.Join(config.XMLDir, event.GroupID)
		file := filepath.Join(dir, event.EventID+"_"+strconv.Itoa(time.Now().Nanosecond())+".xml")
		if _, err := os.Stat(dir); os.IsNotExist(err) {
			err = os.MkdirAll(dir, 0755)
			if err != nil {
				log.Println("Error: failed to create directory", err)
				notify("XBOS PRICE SERVER - Error: failed to create directory, err: "+err.Error(), config.Devtopic, config.Devtopicregion)
				return
			}
		}
		err := ioutil.WriteFile(file, xmlbody, 0600)
		if err != nil {
			log.Println("Error: failed to write xml file", err)
			notify("XBOS PRICE SERVER - Error: failed to write xml file,err: "+err.Error(), config.Devtopic, config.Devtopicregion)
			return
		}
	}

	// if signal parsed properly log extracted prices
	if !config.Logging {
		log.Println("Prices are:", prices, "Target GroupID is:", event.GroupID, "EventID", event.EventID, "Modification Number", event.ModificationNumber)
	}

	// only publish to far events (ignore active or completed events)
	if event.EventStatus == "far" {
		t := event.GroupID + "/"
		if event.SignalName == "ENERGY_PRICE" {
			t += "energy"
		} else {
			t += "demand"
		}
		if !publishPrices(t, prices) {
			http.Error(w, "Error: failed to publish prices to BOSSWAVE", http.StatusInternalServerError)
			return
		}
	}
	// if signal published properly log extracted prices and return OK
	w.WriteHeader(200)
	w.Write([]byte("OK"))
}

// serverRecover recovers from a paniced server
func serverRecover(f func(w http.ResponseWriter, r *http.Request)) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if r := recover(); r != nil {
				log.Println("Panic recovered! err:", r)
				http.Error(w, r.(runtime.Error).Error(), http.StatusInternalServerError)
				notify("XBOS PRICE SERVER - Error: fPanic recovered! err:"+r.(runtime.Error).Error(), config.Devtopic, config.Devtopicregion)
			}
		}()
		f(w, r)
	}
}

// parseXMLBody parses PRICE SIGNAL XML from Pricing Server POST request
// returns a Price slice with the necessary PRICE SIGNAL information, a requestID, and event information
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
				duration := parseDuration(eiEvent.Intervals[i].Duration)
				if duration <= 0 {
					log.Println("duration", duration)
					return nil, EiEvents{}, errors.New("Error: invalid interval duration")
				}
				// ItemUnits will be empty if this is a DEMAND_PRICE signal
				var unit int //default is 0 (not configured)
				if eiEvent.CurrencyPerKWh.ItemUnits == "" {
					if eiEvent.CurrencyPerKW.ItemUnits != "" {
						unit = parseCurrency(eiEvent.CurrencyPerKW.ItemUnits)
					}
				} else {
					unit = parseCurrency(eiEvent.CurrencyPerKWh.ItemUnits)
				}

				prices = append(prices, Price{st.UnixNano(), duration, eiEvent.Intervals[i].Price, unit, time.Now().UnixNano()})
				start = start.Add(time.Duration(duration) * time.Second)
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

// parseDuration parses duration from string (PT1H ... PT24H) or (PT60M ... PT1440M)
// returns -1 if not specified
func parseDuration(d string) int64 {
	s := strings.TrimPrefix(d, "PT")
	if strings.HasSuffix(d, "H") {
		s = strings.TrimSuffix(s, "H")
		val, err := strconv.Atoi(s) // 1 ... 24 OR Error
		if err == nil {
			return 3600 * int64(val)
		} else {
			return -1 // error
		}
	} else if strings.HasSuffix(d, "M") {
		s = strings.TrimSuffix(s, "M")
		val, err := strconv.Atoi(s) // 60, 120, 180, ..., 1440 OR Error
		if err == nil {
			return 60 * int64(val)
		} else {
			return -1 // error
		}
	} else {
		return -1 // error
	}
}

// parseCurrency parses the currency and returns corresponding value as defined in xbos_pricing interface
func parseCurrency(d string) int {
	// 		- value: 0
	// 			description: Not configured
	// 		- value: 1
	// 			description: USD
	if d == "USD" {
		return 1
	} else {
		return 0
	}
}

// publishPrices publishes the prices for a given tariff on the corresponding topic
func publishPrices(tariff string, prices []Price) bool {
	if config.DisableBW {
		return true
	}
	// pge/confirmed/pricing/tariff/s.pricing/PGEA01/energy/i.xbos.pricing/signal/info/
	// sce/confirmed/pricing/tariff/s.pricing/SCE08B/demand/i.xbos.pricing/signal/info/
	topic := ""
	// PGE {FLAT06,PGEA01,PGEA06,PGEA10,PGEE19,PGEE20}
	// SCE {SCE08B,SCETGS3}
	if strings.HasPrefix(tariff, "SCE") {
		topic = "sce"
	} else {
		topic = "pge"
	}
	topic += "/confirmed/pricing/tariff/"
	service := bw2client.RegisterService(topic, "s.pricing")
	iface := service.RegisterInterface(tariff, "i.xbos.pricing")
	po, err := bw2bind.CreateMsgPackPayloadObject(bw2bind.FromDotForm("2.1.1.3"), prices)
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
		notify("XBOS PRICE SERVER - Error: could not publish object, err:"+err.Error(), config.Devtopic, config.Devtopicregion)
		return false
	}
	if config.Logging {
		log.Println("published prices to BW topic", topic+tariff)
	}
	return true
}

// notify notifies developer when something goes wrong using AWS SNS
func notify(msg string, topic string, region string) {
	log.Println(msg)
	if config.DisableNotification {
		log.Println("Notification is disabled")
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
