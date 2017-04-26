package main

import (
	"bufio"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"syscall"

	"github.com/immesys/bw2/objects"
	"github.com/pkg/errors"
	//"github.com/immesys/bw2bind"
)

func fileExists(name string) bool {
	_, err := os.Stat(name)
	return !os.IsNotExist(err)
}

func readEntityFile(name string) (vk string, ent *objects.Entity, err error) {
	contents, err := ioutil.ReadFile(name)
	if err != nil {
		err = errors.Wrap(err, "Could not read file")
		return
	}
	entity, err := objects.NewEntity(int(contents[0]), contents[1:])
	if err != nil {
		err = errors.Wrap(err, "Could not decode entity from file")
		return
	}
	ent, ok := entity.(*objects.Entity)
	if !ok {
		err = errors.New(fmt.Sprintf("File was not an entity: %s", name))
		return
	}
	return objects.FmtKey(ent.GetVK()), ent, nil
}

func diskUsage() float64 {
	var stat syscall.Statfs_t
	wd, err := os.Getwd()
	if err != nil {
		red("Could not get working directory (%s)", err)
	}
	syscall.Statfs(wd, &stat)
	// mb left
	return float64(stat.Bavail*uint64(stat.Bsize)) / 1024.0 / 1024.0
}

func checkLocal() {
	if local == nil || local.db == nil {
		log.Fatalf("XBOS db does not exist at expected location %s. Please run 'xbos init' to create", dbloc)
	}
}

func copyFile(src, dst string) error {
	yellow("Copying %s to %s\n", src, dst)
	file, err := os.Open(src)
	if err != nil {
		return err
	}
	defer file.Close()
	newcopy, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer newcopy.Close()
	if _, err := io.Copy(newcopy, file); err != nil {
		return err
	}
	return nil
}

func deleteFileWithConfirm(file string) (deleted bool) {
	for {
		fmt.Printf("File %s already exists. Delete and make a new one? [y/N]: ", file)
		del := readInput("")
		if del == "Y" || del == "y" {
			if err := os.Remove(file); err != nil {
				log.Fatal(errors.Wrapf(err, "Could not delete file %s", file))
			}
			return true
		} else if del == "N" || del == "n" || del == "" {
			return false
		}
	}
}

func readInput(prompt string) string {
	fmt.Print(prompt)
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		return scanner.Text()
	}
	return ""
}

func continueY(prompt string) bool {
	prompt += " [Y/n]: "
	ans := readInput(prompt)
	return ans == "Y" || ans == "y" || ans == ""
}

func continueN(prompt string) bool {
	prompt += " [y/N]: "
	ans := readInput(prompt)
	return ans == "N" || ans == "n" || ans == ""
}
