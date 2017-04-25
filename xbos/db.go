package main

import (
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
}

func actionInitDB(c *cli.Context) error {
	return initDB(c.String("db"))
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
	client.SetEntityFromEnvironOrExit()
	return &xbosdb{db: db, client: client}
}

func (db *xbosdb) resolveAlias(alias string) (vk string) {
	data, zero, err := db.client.ResolveLongAlias(alias)
	if err != nil {
		log.Fatal(errors.Wrapf(err, "Could not resolve long alias (%s)", alias))
	}
	if zero {
		return alias
	}
	return bw2bind.ToBase64(data)
}
