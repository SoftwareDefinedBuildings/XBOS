package driver

type MsgpackSerializable interface {
	SerializeMsgpack() []byte
}

type XBOSThermostatInfoSignal struct {
	Temperature      float64         `msgpack:"temperature"`
	RelativeHumidity float64         `msgpack:"relative_humidity"`
	HeatingSetpoint  float64         `msgpack:"heating_setpoint"`
	CoolingSetpoint  float64         `msgpack:"cooling_setpoint"`
	Override         bool            `msgpack:"override"`
	Fan              bool            `msgpack:"fan"`
	Mode             ThermostatMode  `msgpack:"mode"`
	State            ThermostatState `msgpack:"state"`
	Time             int64           `msgpack:"time"`
}

// marshal this into a msgpack
func (s XBOSThermostatInfoSignal) SerializeMsgpack() []byte {
	return []byte{}
}
