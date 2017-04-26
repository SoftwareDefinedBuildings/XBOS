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
	var err error
	if err := initDB(path.Join(c.String("local"), "DB")); err != nil {
		return err
	}

	// make entity
	if err := bootstrapEntity("BW2_DEFAULT_ENTITY"); err != nil {
		log.Fatal(err)
	}

	// make bankroll
	if err := bootstrapEntity("BW2_DEFAULT_BANKROLL"); err != nil {
		log.Fatal(err)
	}

	// check if bankroll has $$$
	val := os.Getenv("BW2_DEFAULT_BANKROLL")
	local.vk, err = local.client.SetEntityFile(val)
	if err != nil {
		log.Fatal(err)
	}
	accounts, err := local.client.EntityBalances()
	if err != nil {
		log.Fatal(err)
	}
	balance := weiToCurrency(accounts[0].Int)
	if balance >= 200 {
		green("You have %d Ξ -- enough to continue\n", balance)
	} else {
		red("You do not have enough Ξ! Have a friend run the below command to transfer you some Ether/gas/money, then rerun 'xbos bootstrap'\n")
		fmt.Printf("bw2 xfer -t %s --ether %d\n", accounts[0].Addr, 200-balance)
		c := readInput("Continue? [N/y]: ")
		if c == "N" || c == "n" || c == "" {
			return nil
		}
	}

	// publish entities
	fmt.Println("Publishing $BW2_DEFAULT_ENTITY and $BW2_DEFAULT_BANKROLL")
	pubEntity := exec.Command("bw2", "i", fmt.Sprintf("$BW2_DEFAULT_ENTITY"), "-p")
	if err := pubEntity.Start(); err != nil {
		log.Fatal(errors.Wrap(err, "Could not publish entity"))
	}
	pubBankroll := exec.Command("bw2", "i", fmt.Sprintf("$BW2_DEFAULT_BANKROLL"), "-p")
	if err := pubBankroll.Start(); err != nil {
		log.Fatal(errors.Wrap(err, "Could not publish bankroll"))
	}

	// check if we have an alias already
	local.vk = local.client.SetEntityFromEnvironOrExit()
	alias, key := local.resolveAlias(local.vk)
	if alias != "" {
		yellow("Already have alias %s for $BW2_DEFAULT_ENTITY (%s).\n", alias, key)
		return nil
	}

	makeAlias := readInput("Would you like to make an alias? This will make life easier: [Y/n]")
	if makeAlias == "Y" || makeAlias == "y" || makeAlias == "" {
		var myalias string
		for {
			myalias = readInput("What alphanumeric string would you like to be your alias (typically this is a shortened form of your name)\n: ")
			alias, key = local.resolveAlias(myalias)
			if key != "" {
				red("Alias %s already taken by %s\n", alias, key)
				continue
			}
			break
		}
		fmt.Println("Creating. Will exit when finished")
		out, err := exec.Command("bw2", "mkalias", "--long", myalias, "--b64", local.vk).CombinedOutput()
		fmt.Println(string(out))
		if err != nil {
			log.Fatal(errors.Wrap(err, "Could not create new entity"))
		}
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
		makenew = readInput(fmt.Sprintf("Already have entry for $%s (%s). Want to make a new one? [y/N]: ", varname, oldval))
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
			if err := os.Setenv(varname, newfilepath); err != nil {
				log.Fatal(err)
			}
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
				out, err := exec.Command("bw2", "mke", "-n", "-o", entitydest, "-e", "10y", "-c", fmt.Sprintf("%s", email), "-m", fmt.Sprintf("%s", name)).CombinedOutput()
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
			if err := os.Setenv(varname, newentity); err != nil {
				log.Fatal(err)
			}
			break
		}
	}
	return nil
}
