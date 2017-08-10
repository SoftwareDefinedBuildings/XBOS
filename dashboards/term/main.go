package main

import (
	"fmt"
	"log"
	"math"
	"sync"

	ui "github.com/gizak/termui"
	"github.com/gtfierro/ob"
	"github.com/gtfierro/pundat/client"
	"github.com/pkg/errors"
	bw2 "gopkg.in/immesys/bw2bind.v5"
)

var vk string

func main() {
	client := bw2.ConnectOrExit("")
	client.OverrideAutoChainTo(true)
	vk = client.SetEntityFromEnvironOrExit()

	err := ui.Init()
	if err != nil {
		panic(err)
	}
	defer ui.Close()

	sub, err := newSubscription(subscriptionParams{
		client:  client,
		uuid:    "eefcc515-dbb1-3450-8119-62af42b6266b",
		uri:     "gabe.home/devices/tplink-desk/*/info",
		ponum:   "2.0.0.0/8",
		extract: "power",
		size:    80,
	})
	if err != nil {
		panic(err)
	}

	sub2, err := newSubscription(subscriptionParams{
		client:  client,
		uuid:    "329b483d-cb6f-3fc0-be28-6afa19cc2638",
		uri:     "gabe.home/devices/tplink-kitchen/*/info",
		ponum:   "2.0.0.0/8",
		extract: "power",
		size:    80,
	})
	if err != nil {
		panic(err)
	}

	p := ui.NewPar("ASDFASFDASDF")
	p.Height = 50
	p.Width = 50
	p.TextFgColor = ui.ColorWhite
	p.BorderLabel = "Description"
	p.BorderFg = ui.ColorCyan
	p.Handle("/timer/1s", func(e ui.Event) {
		t := e.Data.(ui.EvtTimer)
		p.Text = fmt.Sprintf("%d %d", t, len(sub.getValues()))
	})

	plot1 := ui.NewLineChart()
	plot1.BorderLabel = "Desk Power (W)"
	plot1.Data = []float64{}
	//plot1.Width = 100
	plot1.Height = 15
	//plot1.X = 50
	//plot1.Y = 0
	plot1.AxesColor = ui.ColorWhite
	plot1.LineColor = ui.ColorYellow | ui.AttrBold
	plot1.Handle("/timer/1s", func(e ui.Event) {
		plot1.Data = sub.getValues()
	})

	plot2 := ui.NewLineChart()
	plot2.BorderLabel = "Kitchen Power (W)"
	plot2.Data = []float64{}
	//plot2.Width = 100
	plot2.Height = 15
	//plot2.X = 100
	//plot2.Y = 0
	plot2.AxesColor = ui.ColorWhite
	plot2.LineColor = ui.ColorYellow | ui.AttrBold
	plot2.Handle("/timer/1s", func(e ui.Event) {
		plot2.Data = sub2.getValues()
	})

	ui.Body.AddRows(
		ui.NewRow(
			ui.NewCol(3, 0, plot1),
			ui.NewCol(3, 0, plot2),
		),
		ui.NewRow(
			ui.NewCol(12, 0, p),
		),
	)
	ui.Body.Align()

	ui.Handle("/sys/kbd/q", func(ui.Event) {
		// press q to quit
		ui.StopLoop()
	})

	draw := func(t int) {
		ui.Body.Align()
		ui.Render(p, plot1, plot2)
	}
	ui.Handle("/timer/1s", func(e ui.Event) {
		t := e.Data.(ui.EvtTimer)
		draw(int(t.Count))
	})

	ui.Loop()
}

type subscription struct {
	c         chan *bw2.SimpleMessage
	valueExpr []ob.Operation
	values    []float64
	size      int
	num       int
	uri       string
	uuid      string
	sync.Mutex
}

func (sub *subscription) getValues() []float64 {
	sub.Lock()
	defer sub.Unlock()
	var f = make([]float64, len(sub.values))
	copy(f, sub.values)
	return f
}

func (sub *subscription) addValues(f []float64) {
	sub.Lock()
	defer sub.Unlock()
	if len(f) > sub.size {
		sub.values = f[:sub.size]
		sub.num = len(f)
	} else if sub.num == sub.size {
		sub.values = append(sub.values[len(f):], f...)
	} else {
		sub.values = append(sub.values, f...)
		sub.num += len(f)
	}
}

type subscriptionParams struct {
	client  *bw2.BW2Client
	uri     string
	ponum   string
	extract string
	size    int
	uuid    string
}

func newSubscription(params subscriptionParams) (*subscription, error) {
	c, err := params.client.Subscribe(&bw2.SubscribeParams{
		URI: params.uri,
	})
	if err != nil {
		return nil, err
	}

	sub := &subscription{
		c:         c,
		valueExpr: ob.Parse(params.extract),
		num:       0,
		size:      params.size,
		uuid:      params.uuid,
		uri:       params.uri,
	}
	pc, err := client.NewPundatClient(params.client, vk, "ucberkeley")
	if err != nil {
		return nil, err
	}
	_, ts, _, err := pc.Query(fmt.Sprintf("select data in (now, now -15min) where uuid = \"%s\"", sub.uuid), 30)
	if err != nil {
		return nil, err
	}
	sub.Lock()
	if len(ts.Data) > 0 {
		vals := ts.Data[0].Values
		if len(vals) > sub.size {
			sub.values = vals[:sub.size]
			sub.num = len(vals[:sub.size])
		} else if len(vals) < sub.size {
			sub.values = vals
			sub.num = len(vals)
		}
	}
	sub.Unlock()

	go func() {
		for msg := range sub.c {
			po := msg.GetOnePODF(params.ponum)
			if po == nil {
				continue
			}
			var thing interface{}
			err := po.(bw2.MsgPackPayloadObject).ValueInto(&thing)
			if err != nil {
				log.Println(errors.Wrap(err, "Could not unmarshal msgpack object"))
				panic(err)
				continue
			}

			// extract the possible value
			value := ob.Eval(sub.valueExpr, thing)
			if value == nil {
				log.Printf("Could  not extract value from %+v", thing)
				panic("no")
				continue
			}
			f64s, err := getFloat64(value)
			if err != nil {
				panic(err)
				log.Println(errors.Wrapf(err, "Could not get float64 values from %+v", value))
				continue
			}
			sub.addValues(f64s)

		}
	}()

	return sub, nil
}

func getFloat64(value interface{}) ([]float64, error) {
	var values []float64
	// generate the timeseries values from our extracted value, and then save it
	// test if the value is a list
	if value_list, ok := value.([]interface{}); ok {
		for _, _val := range value_list {
			value_f64, ok := _val.(float64)
			if !ok {
				if value_u64, ok := value.(uint64); ok {
					value_f64 = float64(value_u64)
				} else if value_i64, ok := value.(int64); ok {
					value_f64 = float64(value_i64)
				} else if value_bool, ok := value.(bool); ok {
					if value_bool {
						value_f64 = float64(1)
					} else {
						value_f64 = float64(0)
					}
				} else {
					return values, fmt.Errorf("Value %+v was not a float64 (was %T)", value, value)
				}
			}
			if math.IsInf(value_f64, 0) || math.IsNaN(value_f64) {
				return values, fmt.Errorf("Invalid number %f", value_f64)
			}
			values = append(values, value_f64)
		}
	} else {
		value_f64, ok := value.(float64)
		if !ok {
			if value_u64, ok := value.(uint64); ok {
				value_f64 = float64(value_u64)
			} else if value_i64, ok := value.(int64); ok {
				value_f64 = float64(value_i64)
			} else if value_bool, ok := value.(bool); ok {
				if value_bool {
					value_f64 = float64(1)
				} else {
					value_f64 = float64(0)
				}
			} else {
				return values, fmt.Errorf("Value %+v was not a float64 (was %T)", value, value)
			}
		}
		if math.IsInf(value_f64, 0) || math.IsNaN(value_f64) {
			return values, fmt.Errorf("Invalid number %f", value_f64)
		}
		values = append(values, value_f64)
	}
	return values, nil
}
