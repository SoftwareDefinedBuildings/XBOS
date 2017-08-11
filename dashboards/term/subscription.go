package main

import (
	"fmt"
	"log"
	"math"
	"sync"

	"github.com/gtfierro/ob"
	"github.com/pkg/errors"
	bw2 "gopkg.in/immesys/bw2bind.v5"
)

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
	uri     string
	ponum   string
	extract string
	size    int
	uuid    string
}

func (d *dash) newSubscription(params subscriptionParams) (*subscription, error) {
	c, err := d.client.Subscribe(&bw2.SubscribeParams{
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
	if sub.uuid != "" {
		_, ts, _, err := d.archiver.Query(fmt.Sprintf("select data in (now, now -30min) where uuid = \"%s\"", sub.uuid), 30)
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
	}

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
