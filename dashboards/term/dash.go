package main

import (
	"fmt"
	"strings"
	"time"

	hod "github.com/gtfierro/hod/clients/go"
	archiver "github.com/gtfierro/pundat/client"
	ui "github.com/gtfierro/termui"
	bw2 "gopkg.in/immesys/bw2bind.v5"
)

type dash struct {
	client   *bw2.BW2Client
	archiver *archiver.PundatClient
	hoddb    *hod.HodClientBW2

	zones map[string]*ui.Row
}

func newDash() *dash {
	d := &dash{
		zones: make(map[string]*ui.Row),
	}
	d.client = bw2.ConnectOrExit("")
	d.client.OverrideAutoChainTo(true)
	vk = d.client.SetEntityFromEnvironOrExit()

	hc, err := hod.NewBW2Client(d.client, "ciee/hod")
	if err != nil {
		panic(err)
	}
	d.hoddb = hc

	pc, err := archiver.NewPundatClient(d.client, vk, "ucberkeley")
	if err != nil {
		panic(err)
	}
	d.archiver = pc

	return d
}

func (d *dash) GetZones() (rows []*ui.Row, bufs []ui.Bufferer) {

	res, err := d.hoddb.DoQuery(zoneQuery, &hod.Options{Timeout: 5 * time.Second})
	if err != nil {
		panic(err)
	}
	temp_subs := d.getThermostatTemperatureSubscriptions()
	hsp_subs := d.getThermostatHSPSubscriptions()
	csp_subs := d.getThermostatCSPSubscriptions()
	room_temps := d.getRoomTemperatures(temp_subs)
	tstat_states := d.getThermostatStateSubscriptions()
	rooms := d.getRooms()
	zone_pars := make(map[string]*ui.Par)
	for _, row := range res.Rows {
		zone := row["?zone"].Value
		if _, found := d.zones[zone]; !found {
			par := ui.NewPar(zone)
			par.Border = true
			par.BorderLabel = zone
			par.Height = 17
			par.Text = "Rooms:\n" + strings.Join(rooms[zone], "\n")
			zone_pars[zone] = par

			state := ui.NewPar(zone)
			state.Border = true
			state.Height = 3
			state.Text = ""
			state.BorderLabel = "Thermostat State"
			state.Handle("/timer/10s", func(e ui.Event) {
				statesub := tstat_states[zone]
				if vals := statesub.getValues(); len(vals) > 0 {
					recent := vals[len(vals)-1]
					if recent == 0 {
						state.Text = "Off"
					} else if recent == 1 {
						state.Text = "[Heating](fg-white,bg-red)"
					} else if recent == 2 {
						state.Text = "[Cooling](fg-white,bg-blue)"
					} else {
						state.Text = "Auto"
					}
				}
			})

			temp_sub := temp_subs[zone]
			hsp_sub := hsp_subs[zone]
			csp_sub := csp_subs[zone]
			temp_plot := ui.NewLineChartMultiple(3)
			temp_plot.BorderLabel = zone
			temp_plot.Height = 20
			temp_plot.AxesColor = ui.ColorWhite
			attr := ui.ColorYellow | ui.AttrBold
			hattr := ui.ColorRed | ui.AttrBold
			cattr := ui.ColorBlue | ui.AttrBold
			temp_plot.LineColors = []ui.Attribute{attr, hattr, cattr}
			temp_plot.Data[0] = temp_sub.getValues()
			temp_plot.Data[1] = hsp_sub.getValues()
			temp_plot.Data[2] = csp_sub.getValues()
			temp_plot.Handle("/timer/1s", func(e ui.Event) {
				temp_plot.Data[0] = temp_sub.getValues()
				temp_plot.Data[1] = hsp_sub.getValues()
				temp_plot.Data[2] = csp_sub.getValues()
			})

			bufs = append(bufs, par)
			bufs = append(bufs, temp_plot)
			bufs = append(bufs, state)
			rowcontents := []*ui.Row{
				ui.NewCol(2, 0, par, state),
				ui.NewCol(4, 0, temp_plot),
			}

			if allgauges, found := room_temps[zone]; found {
				var bs []ui.Bufferer
				for _, b := range allgauges {
					bs = append(bs, ui.Bufferer(b))
				}
				bufs = append(bufs, bs...)

				for len(allgauges) > 6 {
					gauges := allgauges[0:6]
					allgauges = allgauges[6:]
					rowcontents = append(rowcontents, ui.NewCol(3, 0, gauges...))
				}
				rowcontents = append(rowcontents, ui.NewCol(3, 0, allgauges...))
			}

			d.zones[zone] = ui.NewRow(rowcontents...)
		}
	}
	d.getRoomOccupancy(zone_pars)

	for _, row := range d.zones {
		rows = append(rows, row)
	}
	return rows, bufs
}

func (d *dash) getThermostatTemperatureSubscriptions() map[string]*subscription {
	tstats, err := d.hoddb.DoQuery(tstatTempQuery, &hod.Options{Timeout: 5 * time.Second})
	if err != nil {
		panic(err)
	}

	zone_temps := make(map[string]*subscription)

	for _, tstatsensor := range tstats.Rows {
		if _, found := zone_temps[tstatsensor["?zone"].Value]; found {
			continue
		}
		params := subscriptionParams{
			uri:     tstatsensor["?uri"].Value + "/signal/info",
			ponum:   "2.1.1.0/32",
			extract: "temperature",
			size:    80,
			uuid:    tstatsensor["?temp_uuid"].Value,
		}
		sub, err := d.newSubscription(params)
		if err != nil {
			panic(err)
		}
		zone_temps[tstatsensor["?zone"].Value] = sub
	}
	return zone_temps
}
func (d *dash) getThermostatHSPSubscriptions() map[string]*subscription {
	tstats, err := d.hoddb.DoQuery(tstatHSPQuery, &hod.Options{Timeout: 5 * time.Second})
	if err != nil {
		panic(err)
	}

	zone_temps := make(map[string]*subscription)

	for _, tstatsensor := range tstats.Rows {
		if _, found := zone_temps[tstatsensor["?zone"].Value]; found {
			continue
		}
		params := subscriptionParams{
			uri:     tstatsensor["?uri"].Value + "/signal/info",
			ponum:   "2.1.1.0/32",
			extract: "heating_setpoint",
			size:    80,
			uuid:    tstatsensor["?hsp_uuid"].Value,
		}
		sub, err := d.newSubscription(params)
		if err != nil {
			panic(err)
		}
		zone_temps[tstatsensor["?zone"].Value] = sub
	}
	return zone_temps
}
func (d *dash) getThermostatCSPSubscriptions() map[string]*subscription {
	tstats, err := d.hoddb.DoQuery(tstatCSPQuery, &hod.Options{Timeout: 5 * time.Second})
	if err != nil {
		panic(err)
	}

	zone_temps := make(map[string]*subscription)

	for _, tstatsensor := range tstats.Rows {
		if _, found := zone_temps[tstatsensor["?zone"].Value]; found {
			continue
		}
		params := subscriptionParams{
			uri:     tstatsensor["?uri"].Value + "/signal/info",
			ponum:   "2.1.1.0/32",
			extract: "cooling_setpoint",
			size:    80,
			uuid:    tstatsensor["?csp_uuid"].Value,
		}
		sub, err := d.newSubscription(params)
		if err != nil {
			panic(err)
		}
		zone_temps[tstatsensor["?zone"].Value] = sub
	}
	return zone_temps
}
func (d *dash) getThermostatStateSubscriptions() map[string]*subscription {
	tstats, err := d.hoddb.DoQuery(tstatStateQuery, &hod.Options{Timeout: 5 * time.Second})
	if err != nil {
		panic(err)
	}

	zone_states := make(map[string]*subscription)

	for _, tstatsensor := range tstats.Rows {
		if _, found := zone_states[tstatsensor["?zone"].Value]; found {
			continue
		}
		params := subscriptionParams{
			uri:     tstatsensor["?uri"].Value + "/signal/info",
			ponum:   "2.1.1.0/32",
			extract: "state",
			size:    10,
		}
		sub, err := d.newSubscription(params)
		if err != nil {
			panic(err)
		}
		zone_states[tstatsensor["?zone"].Value] = sub
	}
	return zone_states
}

func (d *dash) getRooms() map[string][]string {
	rooms, err := d.hoddb.DoQuery(roomList, &hod.Options{Timeout: 5 * time.Second})
	if err != nil {
		panic(err)
	}

	ret := make(map[string][]string)

	for _, row := range rooms.Rows {
		zone := row["?zone"].Value
		room := row["?room"].Value
		if list, found := ret[zone]; found {
			ret[zone] = append(list, room)
		} else {
			ret[zone] = []string{room}
		}
	}
	return ret
}

func (d *dash) getRoomTemperatures(zonetemps map[string]*subscription) map[string][]ui.GridBufferer {
	room_temp_sensors, err := d.hoddb.DoQuery(roomSensorZoneQuery, &hod.Options{Timeout: 5 * time.Second})
	if err != nil {
		panic(err)
	}

	ret := make(map[string][]ui.GridBufferer)

	for _, row := range room_temp_sensors.Rows {
		zone := row["?zone"].Value
		room := row["?room"].Value
		uri := row["?uri"].Value
		gauge := ui.NewGauge()
		gauge.Height = 3
		gauge.Label = room
		gauge.BarColor = ui.ColorWhite
		gauge.PercentColorHighlighted = ui.ColorBlack

		sub, err := d.newSubscription(subscriptionParams{
			uri:     uri,
			ponum:   "2.0.0.0/8",
			extract: "air_temp",
			size:    1,
		})
		if err != nil {
			panic(err)
		}
		go func() {
			for _ = range time.Tick(1 * time.Second) {
				color := ui.ColorWhite
				zonetemp := float64(-1)
				if zt, found := zonetemps[zone]; found {
					if vals := zt.getValues(); len(vals) > 0 {
						zonetemp = vals[len(vals)-1]
					}
				}
				if vals := sub.getValues(); len(vals) > 0 {
					f := 1.8*vals[len(vals)-1] + 32
					if zonetemp > 0 && f > zonetemp+2 {
						color = ui.ColorRed
					} else if zonetemp > 0 && f < zonetemp-2 {
						color = ui.ColorBlue
					}
					gauge.BarColor = color
					gauge.Percent = int(f)
					gauge.Label = fmt.Sprintf("%s: %.1f", room, f)
				}
			}
		}()
		if list, found := ret[zone]; found {
			ret[zone] = append(list, gauge)
		} else {
			ret[zone] = []ui.GridBufferer{gauge}
		}
	}
	return ret
}

func (d *dash) getRoomOccupancy(zones map[string]*ui.Par) {
	rooms := d.getRooms()
	room_occ_sensors, err := d.hoddb.DoQuery(roomOccSensorZoneQuery, &hod.Options{Timeout: 5 * time.Second})
	if err != nil {
		panic(err)
	}

	ret := make(map[string]*subscription)
	z := make(map[string]string)

	for _, row := range room_occ_sensors.Rows {
		zone := row["?zone"].Value
		room := row["?room"].Value
		uri := row["?uri"].Value

		sub, err := d.newSubscription(subscriptionParams{
			uri:     uri,
			ponum:   "2.0.0.0/8",
			extract: "presence",
			size:    10,
		})
		if err != nil {
			panic(err)
		}
		ret[room] = sub
		z[room] = zone
	}
	go func() {
		for _ = range time.Tick(10 * time.Second) {
			for _, p := range zones {
				p.Text = "Rooms:\n"
			}
			for room, sub := range ret {
				zone := z[room]
				if vals := sub.getValues(); len(vals) > 0 {
					occ := float64(0)
					for _, v := range vals {
						occ += v
					}
					if occ > 0 {
						zones[zone].Text += fmt.Sprintf("[%s](fg-black,bg-white)\n", room)
					} else {
						zones[zone].Text += fmt.Sprintf("%s\n", room)
					}
				} else {
				}
			}
			for _, p := range zones {
				if p.Text == "Rooms:\n" {
					p.Text = "Rooms:\n" + strings.Join(rooms[p.BorderLabel], "\n")
				}
			}
		}
	}()
	return
}
