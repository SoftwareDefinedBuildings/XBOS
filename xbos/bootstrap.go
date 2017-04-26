package main

import (
	"fmt"
	"os"
	"path"

	"github.com/pkg/errors"
	"github.com/urfave/cli"
)

// What needs to happen in the bootstrap process?
// - xbos init
// - create the entity: get the email, full name. Choose expiry for them. Make sure nopublish
// - move the entity to .xbos
// - set BW2_DEFAULT_ENTITY to this entity; set BW2_DEFAULT_BANKROLL to it too
// - produce the command to get money (200 ether), tell them to get someone to run it
// - exit the program. Tell them to rerun when the command has been run (and they have cash)
// - use the detection of BW2_DEFAULT_ENTITY (ensure a copy is in .xbos) to skip to this step
// - ask them for an alias name and register it
// - ask which namespaces and services they want access to

func actionBootstrap(c *cli.Context) error {
	if err := actionInitDB(c); err != nil {
		return err
	}
	var current_default_entity string
	// check if we have a BW2_DEFAULT_ENTITY already
	if val, ok := os.LookupEnv("BW2_DEFAULT_ENTITY"); ok {
		current_default_entity = val
		if path.Dir(current_default_entity) != xbosdir {
			// copy it there!
			newfilepath := path.Join(xbosdir, path.Base(current_default_entity))
			err := copyFile(current_default_entity, newfilepath)
			if err != nil {
				log.Fatal(errors.Wrapf(err, "Trying to copy %s to location %s", current_default_entity, newfilepath))
			}
		}
		// else, its already in the right spot!
	} else {
		// this means that we don't have BW2_DEFAULT_ENTITY set
		// ask the user if they already have one they want to use
		var externalEntity string
		for {
			fmt.Println("Specify the full, absolute path for an entity you'd like to be $BW2_DEFAULT_ENTITY.")
			fmt.Println("Leave this blank if you want me to create an entity for you")
			fmt.Print(": ")
			fmt.Scan(&externalEntity)
			if externalEntity != "" && !fileExists(externalEntity) {
				fmt.Printf("%s doesn't exist. Try another file", externalEntity)
			}
			break
		}
		if externalEntity == "" { //create new entity!
		} else {
		}

		//
	}

	//createEntity := "bw2 mke

	return nil
}
