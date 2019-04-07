package main

import (
	"fmt"
	"github.com/boltdb/bolt"
	"github.com/gtfierro/bw2util"
	"github.com/immesys/bw2/objects"
	"github.com/pkg/errors"
	"github.com/urfave/cli"
)

func actionAddNamespace(c *cli.Context) error {
	checkLocal()
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
	checkLocal()
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
	checkLocal()
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

func actionInspectNamespce(c *cli.Context) error {
	checkLocal()
	if c.NArg() == 0 {
		log.Fatal("Need to specify namespace argument")
	}
	aliasorkey := c.Args().Get(0)
	alias, nsvk := local.resolveAlias(aliasorkey)
	uri := nsvk + "/*"

	// build chains from vk to BW2_DEFAULT_ENTITY
	client, _ := bw2util.NewClient(local.client, local.vk)

	// build all of the chains we can use to subscribe
	_dchains, err := client.FindDOTChains(nsvk)
	if err != nil {
		return errors.Wrap(err, "Could not find DOT chains")
	}
	// get the set of unique URIs for dchains so we can see if they overlap
	var uris []string
	var dchains []*objects.DChain
	for _, dchain := range _dchains {
		// check that the dchain has a valid URI and that its TTL isn't expired
		if suburi := bw2util.GetDChainURI(dchain, uri); len(suburi) > 0 && dchain.GetTTL() >= 0 {
			var found = false
			for _, u := range uris {
				if u == suburi {
					found = true
					break
				}
			}
			if !found {
				uris = append(uris, suburi)
				dchains = append(dchains, dchain)
			}
		}
	}
	fmt.Printf("Permission on namespace %s\n", alias)
	for i, uri := range uris {
		fmt.Println(uri, dchains[i].GetAccessURIPermString())
	}
	return nil
}
