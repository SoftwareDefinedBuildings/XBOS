package main

import (
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
	file, err := os.Open(src)
	if err != nil {
		return errors.Wrapf(err, "Trying to open %s", src)
	}
	defer file.Close()
	newcopy, err := os.Open(dst)
	if err != nil {
		return errors.Wrapf(err, "Trying to copy to location %s", dst)
	}
	defer newcopy.Close()
	if _, err := io.Copy(newcopy, file); err != nil {
		return errors.Wrapf(err, "Trying to copy to location %s", dst)
	}
	return nil
}
