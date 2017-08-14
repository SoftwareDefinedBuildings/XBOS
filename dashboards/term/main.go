package main

import (
	ui "github.com/gtfierro/termui"
	"github.com/urfave/cli"
	"os"
)

var vk string

func main() {
	app := cli.NewApp()
	app.Name = "hvacdash"
	app.Version = "0.0.1"
	app.Usage = "HVAC Dashboard"
	app.Action = run
	app.Flags = []cli.Flag{
		cli.StringFlag{
			Name:   "entity,e",
			Value:  "",
			Usage:  "The entity to use",
			EnvVar: "BW2_DEFAULT_ENTITY",
		},
		cli.StringFlag{
			Name:   "agent,a",
			Usage:  "Local agent address",
			EnvVar: "BW2_AGENT",
		},
		cli.StringFlag{
			Name:  "hod",
			Usage: "HodDB base uri",
			Value: "ciee/hod",
		},
	}
	app.Run(os.Args)
}

func run(c *cli.Context) error {

	d := newDash(c)

	err := ui.Init()
	if err != nil {
		panic(err)
	}
	defer ui.Close()
	rows, zonebufs := d.GetZones()
	ui.Body.AddRows(rows...)

	ui.Handle("/sys/kbd/q", func(ui.Event) {
		// press q to quit
		ui.StopLoop()
	})

	draw := func(t int) {
		ui.Body.Align()
		ui.Render(zonebufs...)
	}
	ui.Handle("/timer/1s", func(e ui.Event) {
		t := e.Data.(ui.EvtTimer)
		draw(int(t.Count))
	})

	ui.Loop()
	return nil
}
