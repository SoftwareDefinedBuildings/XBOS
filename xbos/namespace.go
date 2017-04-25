package main

import (
	"github.com/boltdb/bolt"
	"github.com/urfave/cli"
)

func actionAddNamespace(c *cli.Context) error {
	if c.NArg() == 0 {
		log.Fatal("Need to specify namespace argument")
	}
	local.db.Update(func(tx *bolt.Tx) error {
		//b := tx.Bucket(namespaceBucket)
		log.Debug(local.resolveAlias(c.Args().Get(0)))
		//err := b.Pu
		return nil
	})
	return nil
}

func actionDelNamespace(c *cli.Context) error {
	if c.NArg() == 0 {
		log.Fatal("Need to specify namespace argument")
	}
	return nil
}

func actionListNamespace(c *cli.Context) error {
	if c.NArg() == 0 {
		log.Fatal("Need to specify namespace argument")
	}
	return nil
}
