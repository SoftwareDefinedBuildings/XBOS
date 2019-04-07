package main

import (
	"fmt"

	"github.com/urfave/cli"
)

var docs = map[string]string{
	"bw2": `BOSSWAVE TOOL

Common commands:

# Check BOSSWAVE Status
bw2 status

# Make an entity in file "myentity.ent" that expires in 10 years
bw2 mke -o myentity.ent -c <entity comment> -m <contact info> -e 10y

# Get the VK for an entity
bw2 i <alias or path to entity> # Look for "Entity VK: " line

# Make an alias for VK e.g. Y3-WHr5VQJRxN8r6cCYej3bo4q-rxF_NnfF_74V-4L0=
bw2 mkalias --long <alias> --b64 <vk here>

# Grant subscribe (consume) access on a URI with expiry in 30d
bw2 mkdot -f <path to entity that has permission to grant> -t <recipient entity/alias> -u <uri> -x 'C*' -m <access comment> -c <contact info> -e 30d

# Verify publish access on a URI
bw2 bc -u <uri to check> -x P -t <alias or path to entity to check>

Documentation:
- https://github.com/immesys/bw2#getting-started
- https://github.com/immesys/bw2/wiki
	`,
	"spawnctl": `SPAWNPOINT TOOL

Common commands:

# Scan for spawnpoint instances
spawnctl scan <namespace VK or alias>

Documentation:
- https://github.com/immesys/spawnpoint#spawnpoint
- https://github.com/immesys/spawnpointwiki
- https://github.com/immesys/spawnpoint#interacting-with-spawnpoints-using-spawnctl
`,
	"pundat": `PUNDAT TOOL

Common commands:

# Scan for archivers
pundat scan <namespace VK or alias>

# Start querying
pundat query <base archiver URI>
(pundat)> select data before now where Deployment = "CIEE"

# Verify access to archiver
pundat check -k <alias, VK or path to entity> -u <base archiver URI>

# Check what ranges of data on a URI a key can access
pundat range -k <alias, VK or path to entity> -u <URI where data is published>

- https://github.com/gtfierro/PunDat/wiki
- https://github.com/gtfierro/pundat/wiki/How-to-run-queries
`,
}

func actionDocs(c *cli.Context) error {
	if c.NArg() == 0 {
		yellow("Need to specify one of: pundat, spawnctl, bw2\n")
		return nil
	}
	fmt.Println(docs[c.Args().Get(0)])
	return nil
}
