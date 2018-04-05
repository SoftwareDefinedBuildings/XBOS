package driver

import (
	"encoding/binary"
	"fmt"
	"os"

	"github.com/dgraph-io/badger"
	"github.com/zhangxinngang/murmur"
)

type wal struct {
	db  *badger.DB
	seq *badger.Sequence
	dir string
}

func newWal(dir string) (*wal, error) {
	if err := os.MkdirAll(dir, os.ModeDir|0700); err != nil {
		return nil, err
	}

	opts := badger.DefaultOptions
	opts.Dir = dir
	opts.ValueDir = dir
	opts.SyncWrites = true
	db, err := badger.Open(opts)
	if err != nil {
		return nil, err
	}
	seq, err := db.GetSequence([]byte("wal"), 10)
	if err != nil {
		return nil, err
	}
	w := &wal{
		db:  db,
		dir: dir,
		seq: seq,
	}

	return w, nil
}

func (w *wal) add(uri string, content []byte) (hash []byte, err error) {
	hash = make([]byte, 12)
	err = w.db.Update(func(txn *badger.Txn) error {
		binary.LittleEndian.PutUint32(hash[:4], murmur.Murmur3([]byte(uri)))
		seqno, err := w.seq.Next()
		if err != nil {
			return err
		}
		fmt.Println(seqno)
		binary.LittleEndian.PutUint64(hash[4:], seqno)
		fmt.Println("put", hash)
		return txn.Set(hash, content)
	})
	return
}

func (w *wal) done(hash []byte) error {
	return w.db.Update(func(txn *badger.Txn) error {
		_, err := txn.Get(hash)
		if err == badger.ErrKeyNotFound {
			return nil // nothing to delete
		}
		if err != nil {
			return err
		}
		return txn.Delete(hash)
	})
}

func (w *wal) uncommitted(uri string) (ret [][]byte, err error) {
	opts := badger.DefaultIteratorOptions
	opts.PrefetchSize = 10
	hash := make([]byte, 12)
	urihash := make([]byte, 4)
	_urihash := murmur.Murmur3([]byte(uri))
	binary.LittleEndian.PutUint32(hash[:4], _urihash)
	binary.LittleEndian.PutUint32(urihash, _urihash)
	err = w.db.View(func(txn *badger.Txn) error {
		it := txn.NewIterator(opts)
		for it.Seek(hash); it.ValidForPrefix(urihash); it.Next() {
			item := it.Item()
			v, err := item.Value()
			if err != nil {
				return err
			}
			ret = append(ret, v)
		}
		it.Close()
		return nil
	})
	return
}

func (w *wal) getSeqno(uri string) uint32 {
	return 0
}
