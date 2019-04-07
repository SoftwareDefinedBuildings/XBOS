package virtualthermostat

import (
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/SoftwareDefinedBuildings/XBOS/driver"
	"github.com/immesys/spawnpoint/spawnable"
)

const (
	BASE_TEMP          = 78
	BASE_HSETPOINT     = 60
	BASE_CSETPOINT     = 90
	BASE_MODE          = 3
	E                  = 0.1
	FLUX               = 10
	THERMAL_RESISTANCE = 0.1

	DEW_POINT      = 50.0
	REL_HUMIDITY_A = 5.656854249
	REL_HUMIDITY_B = 0.9659363289
)

type VirtualXBOSThermostatInterface struct {
	name  string
	tstat *VirtualThermostatDriver
}

func (vt *VirtualXBOSThermostatInterface) GetName() string {
	return "i.xbos.thermostat"
}

func (vt *VirtualXBOSThermostatInterface) GetInstance() string {
	return vt.name
}

func (vt *VirtualXBOSThermostatInterface) IsLive() bool {
	return true
}

func (vt *VirtualXBOSThermostatInterface) GetSignals() []string {
	return []string{"info"}
}

func (vt *VirtualXBOSThermostatInterface) Read(signal string) (driver.MsgpackSerializable, error) {
	var state driver.XBOSThermostatInfoSignal
	switch signal {
	case "info":
		vt.tstat.Lock()
		state.Temperature = vt.tstat.temperature
		state.RelativeHumidity = vt.tstat.relativeHumidity
		state.HeatingSetpoint = vt.tstat.heatingSetpoint
		state.CoolingSetpoint = vt.tstat.coolingSetpoint
		state.Override = vt.tstat.override
		state.Fan = vt.tstat.fan
		state.Mode = driver.ThermostatMode(vt.tstat.mode)
		state.State = driver.ThermostatState(vt.tstat.state)
		state.Time = time.Now().UnixNano()
		vt.tstat.Unlock()
	default:
		return state, driver.ErrUnknownSignal
	}
	return state, nil
}

func (vt *VirtualXBOSThermostatInterface) Write(slot string, inp []byte) error {
	// TODO: unpack to setpoints
	switch slot {
	case "setpoint":
		var setpoints driver.XBOSThermostatSetpointSlot
		vt.tstat.Lock()
		vt.tstat.heatingSetpoint = setpoints.HeatingSetpoint
		vt.tstat.coolingSetpoint = setpoints.CoolingSetpoint
		vt.tstat.Unlock()
	case "state":
		var state driver.XBOSThermostatStateSlot
		vt.tstat.Lock()
		vt.tstat.heatingSetpoint = state.HeatingSetpoint
		vt.tstat.coolingSetpoint = state.CoolingSetpoint
		vt.tstat.mode = int(state.Mode)
		vt.tstat.override = state.Override
		vt.tstat.fan = state.Fan
		vt.tstat.Unlock()
	default:
		return driver.ErrUnknownSlot
	}
	return nil
}

type VirtualThermostatDriver struct {
	sync.Mutex
	name       string
	interfaces []driver.Interface

	temperature      float64
	relativeHumidity float64
	heatingSetpoint  float64
	coolingSetpoint  float64
	override         bool
	fan              bool
	mode             int
	state            int
}

func (vt *VirtualThermostatDriver) Initialize(params *spawnable.Params) error {
	vt.name = params.MustString("name")
	vt.interfaces = []driver.Interface{
		&VirtualXBOSThermostatInterface{
			name:  "vt0",
			tstat: vt,
		},
	}
	vt.temperature = BASE_TEMP
	vt.relativeHumidity = 0.0
	vt.heatingSetpoint = BASE_HSETPOINT
	vt.coolingSetpoint = BASE_CSETPOINT
	vt.override = false
	vt.fan = false
	vt.mode = BASE_MODE
	vt.state = BASE_MODE

	go func() {
		for _ = range time.Tick(10 * time.Second) {
			vt.Lock()
			oat := vt.generateOutsideAirTemp()
			cooling, heating := vt.evalTempCondition()
			vt.setState(cooling, heating)
			vt.temperature = vt.generateRoomTemp(oat, cooling, heating)
			vt.relativeHumidity = vt.generateRelativeHumidity(vt.temperature)
			vt.Unlock()
		}
	}()
	return nil
}

func (vt *VirtualThermostatDriver) GetName() string {
	return vt.name
}

func (vt *VirtualThermostatDriver) GetInterfaces() []driver.Interface {
	return vt.interfaces
}

func (vt *VirtualThermostatDriver) generateOutsideAirTemp() float64 {
	currentTime := time.Now()
	currentTimeSeconds := float64((currentTime.Hour() * 3600) + (currentTime.Minute() * 60) + currentTime.Second())
	fmt.Println(currentTimeSeconds)
	temp := BASE_TEMP + (FLUX * math.Sin(0.01*currentTimeSeconds))
	return temp
}

func (vt *VirtualThermostatDriver) generateRelativeHumidity(temp float64) float64 {
	if temp < DEW_POINT {
		temp = DEW_POINT
	}
	return REL_HUMIDITY_A * math.Pow(REL_HUMIDITY_B, temp)
}

func (vt *VirtualThermostatDriver) generateRoomTemp(outsideAirTemp float64, cooling int, heating int) float64 {
	deltaT := outsideAirTemp - vt.temperature
	temp := vt.temperature + (THERMAL_RESISTANCE * deltaT) - (float64(cooling) * E * deltaT) + (float64(heating) * E * deltaT) //T + (thermal_resistance * delta_t) - (cooling * e * delta_t) + (heat * e * delta_t)
	return temp
}

func (vt *VirtualThermostatDriver) evalTempCondition() (cooling int, heating int) {
	if vt.temperature < vt.heatingSetpoint {
		heating = 1
	} else if vt.temperature > vt.coolingSetpoint {
		cooling = 1
	}

	switch vt.mode {
	case 0:
		cooling, heating = 0, 0
	case 1:
		cooling = 0
	case 2:
		heating = 0
	case 3:
		break
	}
	return
}

func (vt *VirtualThermostatDriver) setState(cooling int, heating int) {
	if cooling == 0 && heating == 0 {
		if vt.mode == 0 {
			vt.state = 0
		} else {
			vt.state = 3
		}
	} else if cooling == 0 && heating == 1 {
		vt.state = 1
	} else if cooling == 1 && heating == 0 {
		vt.state = 2
	}
}
