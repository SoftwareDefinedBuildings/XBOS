package main

import (
	ui "github.com/gtfierro/termui"
)

var vk string

func main() {
	//client := bw2.ConnectOrExit("")
	//client.OverrideAutoChainTo(true)
	//vk = client.SetEntityFromEnvironOrExit()

	d := newDash()

	err := ui.Init()
	if err != nil {
		panic(err)
	}
	defer ui.Close()

	//sub, err := newSubscription(subscriptionParams{
	//	client:  client,
	//	uuid:    "eefcc515-dbb1-3450-8119-62af42b6266b",
	//	uri:     "gabe.home/devices/tplink-desk/*/info",
	//	ponum:   "2.0.0.0/8",
	//	extract: "power",
	//	size:    80,
	//})
	//if err != nil {
	//	panic(err)
	//}

	//sub2, err := newSubscription(subscriptionParams{
	//	client:  client,
	//	uuid:    "329b483d-cb6f-3fc0-be28-6afa19cc2638",
	//	uri:     "gabe.home/devices/tplink-kitchen/*/info",
	//	ponum:   "2.0.0.0/8",
	//	extract: "power",
	//	size:    80,
	//})
	//if err != nil {
	//	panic(err)
	//}

	//p := ui.NewPar(fmt.Sprintf("%s", res))
	//p.Height = 50
	//p.Width = 50
	//p.TextFgColor = ui.ColorWhite
	//p.BorderLabel = "Description"
	//p.BorderFg = ui.ColorCyan
	//p.Handle("/timer/1s", func(e ui.Event) {
	//	t := e.Data.(ui.EvtTimer)
	//	p.Text = fmt.Sprintf("%d %d", t, len(sub.getValues()))
	//})

	//plot1 := ui.NewLineChart()
	//plot1.BorderLabel = "Desk Power (W)"
	//plot1.Data = []float64{}
	////plot1.Width = 100
	//plot1.Height = 15
	////plot1.X = 50
	////plot1.Y = 0
	//plot1.AxesColor = ui.ColorWhite
	//plot1.LineColor = ui.ColorYellow | ui.AttrBold
	//plot1.Handle("/timer/1s", func(e ui.Event) {
	//	plot1.Data = sub.getValues()
	//})

	//plot2 := ui.NewLineChart()
	//plot2.BorderLabel = "Kitchen Power (W)"
	//plot2.Data = []float64{}
	////plot2.Width = 100
	//plot2.Height = 15
	////plot2.X = 100
	////plot2.Y = 0
	//plot2.AxesColor = ui.ColorWhite
	//plot2.LineColor = ui.ColorYellow | ui.AttrBold
	//plot2.Handle("/timer/1s", func(e ui.Event) {
	//	plot2.Data = sub2.getValues()
	//})

	//ui.Body.AddRows(
	//	ui.NewRow(
	//		ui.NewCol(3, 0, plot1),
	//		ui.NewCol(3, 0, plot2),
	//	),
	//	ui.NewRow(
	//		ui.NewCol(12, 0, p),
	//	),
	//)
	//ui.Body.Align()
	//d.GetZones()
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
}
