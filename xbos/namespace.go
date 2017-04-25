package main

import (
	"fmt"
	"github.com/boltdb/bolt"
	"github.com/urfave/cli"
)

func actionAddNamespace(c *cli.Context) error {
	if c.NArg() == 0 {
		log.Fatal("Need to specify namespace argument")
	}
	aliasorkey := c.Args().Get(0)
	err := local.db.Update(func(tx *bolt.Tx) error {
		alias, vk := local.resolveAlias(aliasorkey)
		b := tx.Bucket(namespaceBucket)
		fmt.Printf("Adding %s => %s\n", alias, vk)
		return b.Put([]byte(alias), []byte(vk))
	})
	return err
}

func actionDelNamespace(c *cli.Context) error {
	if c.NArg() == 0 {
		log.Fatal("Need to specify namespace argument")
	}
	aliasorkey := c.Args().Get(0)
	err := local.db.Update(func(tx *bolt.Tx) error {
		alias, vk := local.resolveAlias(aliasorkey)
		b := tx.Bucket(namespaceBucket)
		fmt.Printf("Deleting %s (%s)\n", alias, vk)
		return b.Delete([]byte(alias))
	})
	return err
}

func actionListNamespace(c *cli.Context) error {
	err := local.db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket(namespaceBucket)
		c := b.Cursor()
		for k, v := c.First(); k != nil; k, v = c.Next() {
			fmt.Printf("%s => %s\n", string(k), string(v))
		}
		return nil
	})
	return err
}
