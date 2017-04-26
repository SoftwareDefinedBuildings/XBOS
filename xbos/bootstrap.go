package main

import (
	"fmt"
	"os"
	"os/exec"
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
	if err := initDB(path.Join(c.String("local"), "DB")); err != nil {
		return err
	}

	if err := bootstrapEntity("BW2_DEFAULT_ENTITY"); err != nil {
		log.Fatal(err)
	}
	if err := bootstrapEntity("BW2_DEFAULT_BANKROLL"); err != nil {
		log.Fatal(err)
	}

	return nil
}

func bootstrapEntity(varname string) error {
	var current_entity string
	// check if we have a [varname] already
	var makenew string
	var oldval string
	var ok bool
	if oldval, ok = os.LookupEnv(varname); ok {
		makenew = readInput(fmt.Sprintf("Already have entry for $%s. Want to make a new one? [y/N]: ", varname))
	}

	if (makenew == "N" || makenew == "n" || makenew == "") && ok {
		current_entity = oldval
		if path.Dir(current_entity) != xbosdir {
			// copy it there!
			newfilepath := path.Join(xbosdir, path.Base(current_entity))
			err := copyFile(current_entity, newfilepath)
			if err != nil {
				log.Fatal(errors.Wrapf(err, "Trying to copy %s to location %s", current_entity, newfilepath))
			}
			green("Add the following lines to your .bashrc:\n")
			fmt.Printf("export %s=%s\n", varname, newfilepath)
			fmt.Println()
		}
		// else, its already in the right spot!
	} else {
		// this means that we don't have [varname] set
		// ask the user if they already have one they want to use
		var externalEntity string
		for {
			fmt.Printf("Specify the full, absolute path for an entity you'd like to be %s.\n", varname)
			fmt.Println("Leave this blank if you want me to create an entity for you")
			externalEntity = readInput(": ")
			if externalEntity != "" && !fileExists(externalEntity) {
				fmt.Printf("%s doesn't exist. Try another file\n", externalEntity)
				continue
			}
			var newentity string
			if externalEntity == "" { //create new entity!
				entitydest := path.Join(xbosdir, "default.ent")
				name := readInput("Your name: ")
				email := readInput("Your email: ")
				out, err := exec.Command("bw2", "mke", "-n", "-o", entitydest, "-e", "10y", "-c", fmt.Sprintf("'%s'", email), "-m", fmt.Sprintf("'%s'", name)).CombinedOutput()
				if err != nil {
					fmt.Println(string(out))
					log.Fatal(errors.Wrap(err, "Could not create new entity"))
				}
				newentity = entitydest
			} else {
				newfilepath := path.Join(xbosdir, path.Base(externalEntity))
				err := copyFile(externalEntity, newfilepath)
				if err != nil {
					log.Fatal(errors.Wrapf(err, "Trying to copy %s to location %s", current_entity, newfilepath))
				}
				newentity = newfilepath
			}

			green("Add the following lines to your .bashrc:\n")
			fmt.Printf("export %s=%s\n", varname, newentity)
			fmt.Println()
			break
		}
	}
	return nil
}
