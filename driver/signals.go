//go:generate msgp
package driver

import (
	bw2 "github.com/immesys/bw2bind"
)

const (
	XBOS_THERMOSTAT_PONUM_DOT = "2.1.1.0"
	XBOS_WAL_PONUM_DOT        = "2.9.9.9"
)

var (
	XBOS_THERMOSTAT_PONUM = bw2.FromDotForm(XBOS_THERMOSTAT_PONUM_DOT)
	XBOS_WAL_PONUM        = bw2.FromDotForm(XBOS_WAL_PONUM_DOT)
)

type MsgpackSerializable interface {
	SerializeMsgpack() []byte
	GetPONum() int
}

type XBOSThermostatInfoSignal struct {
	Temperature      float64         `msg:"temperature"`
	RelativeHumidity float64         `msg:"relative_humidity"`
	HeatingSetpoint  float64         `msg:"heating_setpoint"`
	CoolingSetpoint  float64         `msg:"cooling_setpoint"`
	Override         bool            `msg:"override"`
	Fan              bool            `msg:"fan"`
	Mode             ThermostatMode  `msg:"mode"`
	State            ThermostatState `msg:"state"`
	Time             int64           `msg:"time"`
}

// marshal this into a msgpack
func (s XBOSThermostatInfoSignal) SerializeMsgpack() []byte {
	data, _ := s.MarshalMsg(nil)
	return data
}

func (s XBOSThermostatInfoSignal) GetPONum() int {
	return XBOS_THERMOSTAT_PONUM
}
