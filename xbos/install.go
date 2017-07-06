package main

import (
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"runtime"

	"github.com/urfave/cli"
)

func actionInstallAgent(c *cli.Context) error {
	if continueY("Installing BOSSWAVE Agent. Continue?") {
		yellow("Running! This may take a few minutes\n")
		curlout, err := exec.Command("bash", "-c", "curl get.bw2.io/agent").Output()
		if err != nil {
			red("Could not install BOSSWAVE Agent (%v)\n", err)
			return nil
		}

		tmpfile, err := ioutil.TempFile("", "installagent.sh")
		if err != nil {
			log.Fatal(err)
		}
		if _, err := tmpfile.Write(curlout); err != nil {
			log.Fatal(err)
		}
		if err := tmpfile.Close(); err != nil {
			log.Fatal(err)
		}

		log.Debug(tmpfile.Name())
		output, err := exec.Command("bash", tmpfile.Name()).CombinedOutput()
		fmt.Print(string(output))
		if err != nil {
			red("Could not install BOSSWAVE Agent (%v)\n", err)
			return nil
		}
		green("Installed BOSSWAVE Agent! Read the output and run any required commands and wait for the chain to catch up. Remember you can run 'xbos doctor' to quickly verify that everything's working")
		green(" To use, run\nbw2\n")
		os.Remove(tmpfile.Name())
	}
	return nil
}

func actionInstallSpawnctl(c *cli.Context) error {
	if continueY("Installing Spawnpoint CLI tool Continue?") {
		yellow("Running! This may take a few minutes\n")
		output, err := exec.Command("go", "get", "-u", "github.com/immesys/spawnpoint/spawnctl").CombinedOutput()
		fmt.Print(string(output))
		if err != nil {
			red("Could not fetch spawnctl (%v)\n", err)
			return nil
		}
		output, err = exec.Command("go", "install", "github.com/immesys/spawnpoint/spawnctl").CombinedOutput()
		fmt.Print(string(output))
		if err != nil {
			red("Could not install spawnctl (%v)\n", err)
			return nil
		}
		green("Installed spawnctl!")
		green(" To use, run\nspawnctl\n")
	}
	return nil
}
func actionInstallPundat(c *cli.Context) error {
	actionInstallBosswavePrereqs()
	if continueY("Installing Archiver CLI tool Continue?") {
		yellow("Running! This may take a few minutes\n")
		output, err := exec.Command("go", "get", "-u", "github.com/gtfierro/pundat").CombinedOutput()
		fmt.Print(string(output))
		if err != nil {
			red("Could not fetch pundat (%v)\n", err)
			return nil
		}
		output, err = exec.Command("go", "install", "github.com/gtfierro/pundat").CombinedOutput()
		fmt.Print(string(output))
		if err != nil {
			red("Could not install pundat (%v)\n", err)
			return nil
		}
		green("Installed pundat!")
		green(" To use, run\npundat\n")
	}
	return nil
}
func actionInstallRagent(c *cli.Context) error {
	yellow("Support for installing ragent is not supported yet\n")
	return nil
}

func actionInstallBosswavePrereqs() error {
	// install gcc
	green(runtime.GOOS)
	if runtime.GOOS == "linux" {
		output, err := exec.Command("apt-get", "update", "-y").CombinedOutput()
		if err != nil {
			red("Could not update apt-get (%v)\n", err)
			return nil
		}
		fmt.Print(string(output))
		output, err = exec.Command("apt-get", "install", "-y", "build-essential", "libssl-dev").CombinedOutput()
		if err != nil {
			red("Could not update apt-get install build-essential(%v)\n", err)
			return nil
		}
		fmt.Print(string(output))
	}

	// install golang
	if runtime.GOOS == "linux" {
		output, err := exec.Command("wget", "https://storage.googleapis.com/golang/go1.8.3.linux-amd64.tar.gz").CombinedOutput()
		if err != nil {
			red("Could not download go tar file (%v)\n", err)
			return nil
		}
		fmt.Print(string(output))
		output, err = exec.Command("tar", "-C", "/usr/local", "-xzf", "go1.8.3.linux-amd64.tar.gz").CombinedOutput()
		if err != nil {
			red("Could not install go (%v)\n", err)
			return nil
		}
		fmt.Print(string(output))
	}
	return nil
}
