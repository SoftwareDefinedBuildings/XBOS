package driver

type XBOSThermostatSetpointSlot struct {
	HeatingSetpoint float64 `msgpack:"heating_setpoint"`
	CoolingSetpoint float64 `msgpack:"cooling_setpoint"`
}

type XBOSThermostatStateSlot struct {
	HeatingSetpoint float64        `msgpack:"heating_setpoint"`
	CoolingSetpoint float64        `msgpack:"cooling_setpoint"`
	Override        bool           `msgpack:"override"`
	Fan             bool           `msgpack:"fan"`
	Mode            ThermostatMode `msgpack:"mode"`
}
