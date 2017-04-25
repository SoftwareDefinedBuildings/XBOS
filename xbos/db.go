package main

import (
	"path"
	"strings"

	"github.com/boltdb/bolt"
	"github.com/immesys/bw2bind"
	"github.com/pkg/errors"
	"github.com/urfave/cli"
)

var (
	namespaceBucket = []byte("namespace")
	keyBucket       = []byte("key")
)

type xbosdb struct {
	db     *bolt.DB
	client *bw2bind.BW2Client
	vk     string
}

func actionInitDB(c *cli.Context) error {
	return initDB(path.Join(c.String("local"), "DB"))
}

func initDB(dbloc string) error {
	db, err := bolt.Open(dbloc, 0600, nil)
	if err != nil {
		log.Fatal(errors.Wrapf(err, "Could not open XBOS db at %s", dbloc))
	}
	defer db.Close()

	// create buckets
	err = db.Update(func(tx *bolt.Tx) error {
		buckets := [][]byte{namespaceBucket, keyBucket}
		for _, bucket := range buckets {
			_, err := tx.CreateBucket(bucket)
			if err != nil {
				return errors.Wrapf(err, "Could not create bucket %s", bucket)
			}
		}
		return nil
	})
	if err != nil {
		log.Fatal(errors.Wrapf(err, "Could not create XBOS db at %s", dbloc))
	}
	return nil
}

func getDB(dbloc string) *xbosdb {
	db, err := bolt.Open(dbloc, 0600, nil)
	if err != nil {
		log.Fatal(errors.Wrapf(err, "Could not open XBOS db at %s", dbloc))
	}
	client, err := bw2bind.Connect("")
	if err != nil {
		log.Fatal(errors.Wrap(err, "Could not connect to $BW2_AGENT"))
	}
	vk := client.SetEntityFromEnvironOrExit()
	return &xbosdb{db: db, client: client, vk: vk}
}

func (db *xbosdb) resolveAlias(aliasorkey string) (alias, vk string) {
	data, zero, err := db.client.ResolveLongAlias(aliasorkey)
	if err != nil {
		//if we cannot resolve long alias, try unresolving
		if strings.HasPrefix(err.Error(), "[513]") {
			bb, err := bw2bind.FromBase64(aliasorkey)
			if err != nil {
				log.Fatal(errors.Wrapf(err, "Could not convert %s to base64", aliasorkey))
			}
			actualalias, err := db.client.UnresolveAlias(bb)
			if err != nil {
				log.Fatal(errors.Wrapf(err, "Could not unresolve alias %s", aliasorkey))
			}
			return actualalias, aliasorkey
		}
		log.Fatal(errors.Wrapf(err, "Could not resolve long alias (%s)", aliasorkey))
	}
	if zero {
		return aliasorkey, aliasorkey
	}
	return aliasorkey, bw2bind.ToBase64(data)
}

func (db *xbosdb) getNamespaces() []string {
	var namespaces []string
	err := local.db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket(namespaceBucket)
		c := b.Cursor()
		for k, v := c.First(); k != nil; k, v = c.Next() {
			namespaces = append(namespaces, string(v))
		}
		return nil
	})
	if err != nil {
		log.Fatal(errors.Wrap(err, "Could not get namespaces"))
	}
	return namespaces
}
