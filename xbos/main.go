package main

import (
	"github.com/urfave/cli"
	"os"
)

func main() {
	app := cli.NewApp()
	app.Name = "xbos"
	app.Version = "0.0.1"
	app.Usage = "XBOS command line tool"

	app.Commands = []cli.Command{
		{
			Name:   "doctor",
			Usage:  "Run a check of common issues and print out a diagnosis",
			Action: doctor,
		},
	}
	app.Run(os.Args)
}
