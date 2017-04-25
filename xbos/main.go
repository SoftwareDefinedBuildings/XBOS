package main

import (
	"os"
	"os/user"
	"path"

	"github.com/op/go-logging"
	"github.com/urfave/cli"
)

// logger
var log *logging.Logger
var userHome string
var local *xbosdb

func init() {
	log = logging.MustGetLogger("xbos")
	var format = "%{color}%{level} %{shortfile} %{time:Jan 02 15:04:05} %{color:reset} ▶ %{message}"
	var logBackend = logging.NewLogBackend(os.Stderr, "", 0)
	logBackendLeveled := logging.AddModuleLevel(logBackend)
	logging.SetBackend(logBackendLeveled)
	logging.SetFormatter(logging.MustStringFormatter(format))

	curuser, err := user.Current()
	if err != nil {
		log.Fatal(err)
	}
	userHome = curuser.HomeDir

	dbloc := path.Join(userHome, ".xbos.db")
	if val, ok := os.LookupEnv("XBOS_LOCAL_DB"); ok {
		dbloc = val
	}
	if !fileExists(dbloc) {
		log.Warningf("XBOS db does not exist at expected location %s. Please run 'xbos init' to create", dbloc)
	} else {
		local = getDB(dbloc)
	}

}

func main() {
	app := cli.NewApp()
	app.Name = "xbos"
	app.Version = "0.0.2"
	app.Usage = "XBOS command line tool"

	app.Commands = []cli.Command{
		{
			Name:   "init",
			Usage:  "Initialize XBOS state on your machine",
			Action: actionInitDB,
			Flags: []cli.Flag{
				cli.StringFlag{
					Name:   "db",
					Usage:  "Location for local XBOS state",
					Value:  path.Join(userHome, ".xbos.db"),
					EnvVar: "XBOS_LOCAL_DB",
				},
			},
		},
		{
			Name:   "doctor",
			Usage:  "Run a check of common issues and print out a diagnosis",
			Action: actionDoctor,
		},
		{
			Name:    "namespace",
			Aliases: []string{"ns"},
			Usage:   "Manage default namespaces",
			Subcommands: []cli.Command{
				{
					Name:   "add",
					Usage:  "Add namespace",
					Action: actionAddNamespace,
				},
				{
					Name:   "del",
					Usage:  "Delete namespace",
					Action: actionDelNamespace,
				},
				{
					Name:   "list",
					Usage:  "List namespaces",
					Action: actionListNamespace,
				},
			},
		},
	}
	app.Run(os.Args)
}
