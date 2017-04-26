package main

import (
	"fmt"
	"os/exec"
	"strings"

	"github.com/urfave/cli"
)

type serviceDefinition struct {
	ServiceName  string
	FoundService func(ns string) bool
}

var checkSpawnpoint = serviceDefinition{
	ServiceName: "spawnpoint",
	FoundService: func(ns string) bool {
		cmd := exec.Command("spawnctl", "scan", ns)
		out, _ := cmd.CombinedOutput()
		return strings.Contains(string(out), "Available Memory")
	},
}

var checkArchiver = serviceDefinition{
	ServiceName: "archiver",
	FoundService: func(ns string) bool {
		cmd := exec.Command("pundat", "scan", ns)
		out, _ := cmd.CombinedOutput()
		return strings.Contains(string(out), "Found Archiver at:")
	},
}

var services = map[string]serviceDefinition{
	"spawnpoint": checkSpawnpoint,
	"pundat":     checkArchiver,
}

func findService(c *cli.Context) error {
	checkLocal()
	if c.NArg() == 0 {
		log.Fatal("Need to specify service argument. One of: pundat, spawnpoint")
	}
	namespaces := c.StringSlice("namespaces")
	if len(namespaces) == 0 {
		namespaces = local.getNamespaces()
	}

	if len(namespaces) == 0 {
		yellow("No namespaces configured. Try specifying some or adding defaults via `xbos ns add`\n")
	}

	for _, ns := range namespaces {
		alias, vk := local.resolveAlias(ns)
		svc := services[c.Args().Get(0)]
		if svc.FoundService(vk) {
			fmt.Printf("Found service %s on namespace %s (%s)\n", svc.ServiceName, alias, vk)
		}
	}

	return nil
}
