package main

import (
	"os"
	"os/user"
	"path"

	"github.com/op/go-logging"
	"github.com/pkg/errors"
	"github.com/urfave/cli"
)

// logger
var log *logging.Logger
var userHome string
var xbosdir string
var dbloc string
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

	xbosdir = path.Join(userHome, ".xbos")
	if val, ok := os.LookupEnv("XBOS_LOCAL_DIR"); ok {
		xbosdir = val
	}
	if !fileExists(xbosdir) {
		log.Warningf("XBOS directory does not exist at expected location %s. Creating...", xbosdir)
		err := os.MkdirAll(xbosdir, 0755)
		if err != nil {
			log.Fatal(errors.Wrapf(err, "Could not create local XBOS dir at %s", xbosdir))
		}
	}

	dbloc = path.Join(xbosdir, "DB")
	if !fileExists(dbloc) {
		log.Warningf("XBOS db does not exist at expected location %s. Please run 'xbos init' to create", dbloc)
	} else {
		local = getDB(dbloc)
	}

}

func main() {
	app := cli.NewApp()
	app.Name = "xbos"
	app.Version = "0.0.3"
	app.Usage = "XBOS command line tool"

	app.Commands = []cli.Command{
		{
			Name:   "init",
			Usage:  "Initialize XBOS state on your machine",
			Action: actionInitDB,
			Flags: []cli.Flag{
				cli.StringFlag{
					Name:   "local",
					Usage:  "Location for local XBOS state",
					Value:  path.Join(userHome, ".xbos"),
					EnvVar: "XBOS_LOCAL_DIR",
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
				{
					Name:    "inspect",
					Aliases: []string{"i"},
					Usage:   "Inspect permissions on namespace",
					Action:  actionInspectNamespce,
				},
			},
		},
		{
			Name:  "find",
			Usage: "Find XBOS services",
			Flags: []cli.Flag{
				cli.StringSliceFlag{
					Name:  "namespaces, ns",
					Usage: "List of namespaces to scan for the given service. Defaults to your registered namespaces",
				},
			},
			Action: findService,
		},
		{
			Name:   "bootstrap",
			Usage:  "Get a new user started with BOSSWAVE",
			Action: actionBootstrap,
			Flags: []cli.Flag{
				cli.StringFlag{
					Name:   "local",
					Usage:  "Location for local XBOS state",
					Value:  path.Join(userHome, ".xbos"),
					EnvVar: "XBOS_LOCAL_DIR",
				},
			},
		},
		{
			Name:  "install",
			Usage: "Installs/updates BOSSWAVE software for the user",
			Subcommands: []cli.Command{
				{
					Name:   "agent",
					Usage:  "Installs BOSSWAVE agent",
					Action: actionInstallAgent,
				},
				{
					Name:   "ragent",
					Usage:  "Installs BOSSWAVE remote agent",
					Action: actionInstallRagent,
				},
				{
					Name:   "spawnctl",
					Usage:  "Installs spawnpoint cli tool",
					Action: actionInstallSpawnctl,
				},
				{
					Name:   "pundat",
					Usage:  "Installs pundat cli tool",
					Action: actionInstallPundat,
				},
			},
		},
	}
	app.Run(os.Args)
}
