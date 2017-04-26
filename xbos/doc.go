package main

import (
	"fmt"

	"github.com/urfave/cli"
)

var docs = map[string][]string{
	"bw2": []string{
		"https://github.com/immesys/bw2#getting-started",
		"https://github.com/immesys/bw2/wiki",
	},
	"spawnctl": []string{
		"https://github.com/immesys/spawnpoint#spawnpoint",
		"https://github.com/immesys/spawnpointwiki",
		"https://github.com/immesys/spawnpoint#interacting-with-spawnpoints-using-spawnctl",
	},
	"pundat": []string{
		"https://github.com/gtfierro/PunDat/wiki",
		"https://github.com/gtfierro/pundat/wiki/How-to-run-queries",
	},
}

func actionDocs(c *cli.Context) error {
	if c.NArg() == 0 {
		yellow("Need to specify one of: pundat, spawnctl, bw2\n")
		return nil
	}
	for _, doc := range docs[c.Args().Get(0)] {
		fmt.Println(doc)
	}
	return nil
}
