package main

import (
	"github.com/SoftwareDefinedBuildings/XBOS/driver"
	"github.com/SoftwareDefinedBuildings/XBOS/driver/drivers/virtual_thermostat"
)

func main() {
	vt := virtualthermostat.VirtualThermostatDriver{}

	exec := driver.BW2DriverExecutor{}
	exec.Run(&vt)
}
