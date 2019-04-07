package driver

import (
	"encoding/base64"
	"fmt"
	"sync"
	"time"

	bw2 "github.com/immesys/bw2bind"
	"github.com/immesys/spawnpoint/spawnable"
	"github.com/pkg/errors"
)

type Driver interface {
	// Initialize the driver with configuration
	Initialize(*spawnable.Params) error

	// Get the name of the driver
	GetName() string

	// return the interfaces implemented by this driver
	GetInterfaces() []Interface
}

type BW2DriverExecutor struct {
	d       Driver
	cl      sync.Mutex
	client  *bw2.BW2Client
	baseURI string
	wal     *wal

	interfaceLock sync.RWMutex
	interfaces    map[string]Interface
}

// Configuration needed for BW2 Driver:
// - base URI
// - entity file
// - interface refresh rate

func (exec *BW2DriverExecutor) Run(driver Driver) (err error) {
	//var entityFile string = "asdf"
	var interfaceRefreshRate time.Duration = 30 * time.Second
	var livenessInterval time.Duration = 10 * time.Second
	var pollingInterval time.Duration = 1 * time.Second

	params := spawnable.GetParamsOrExit()
	if err := driver.Initialize(params); err != nil {
		return errors.Wrap(err, "Could not initialize with params")
	}

	exec.d = driver
	exec.wal, err = newWal("_wal")
	if err != nil {
		return errors.Wrap(err, "Could not init WAL")
	}
	exec.cl.Lock()
	exec.client = bw2.ConnectOrExit("")
	exec.client.OverrideAutoChainTo(true)
	exec.client.SetEntityFromEnvironOrExit()
	exec.interfaces = make(map[string]Interface)
	exec.baseURI = params.MustString("base_uri")
	exec.client.SetErrorHandler(func(e error) {
		fmt.Println("Error!", e)
		for e != nil {
			time.Sleep(5 * time.Second)
			exec.cl.Lock()
			fmt.Println("Attempt reconnect")
			exec.client, e = bw2.Connect("")
			exec.cl.Unlock()
		}
	})
	exec.cl.Unlock()

	name := driver.GetName()
	fmt.Println("Driver name is", name)

	// refresh interfaces periodically
	go func() {
		exec.refreshInterfaces()
		for _ = range time.Tick(interfaceRefreshRate) {
			exec.refreshInterfaces()
		}
	}()

	// publish liveness messages for interfaces
	go func() {
		for _ = range time.Tick(livenessInterval) {
			exec.interfaceLock.RLock()
			for _, iface := range exec.interfaces {
				if iface.IsLive() {
					exec.publishLiveness(iface)
					fmt.Println(iface.GetName(), iface.GetInstance(), "is alive")
				}
			}
			exec.interfaceLock.RUnlock()
		}
	}()

	// publish read data
	go func() {
		for _ = range time.Tick(pollingInterval) {
			exec.interfaceLock.RLock()
			for _, iface := range exec.interfaces {
				if iface.IsLive() {
					exec.publishSignals(iface)
				}
			}
			exec.interfaceLock.RUnlock()
		}
	}()

	//readUncommitted := func(seqno int) []byte {
	//}
	//subscribeURI := fmt.Sprintf("%s/s.%s/%s/i.xbos.wal/slot/log",
	//	exec.baseURI,
	//	exec.d.GetName(),
	//	iface.GetInstance(),
	//)
	//sub, err := exec.client.Subscribe(&bw2.SubscribeParams{
	//	URI: subscribeURI,
	//})
	//if err != nil {
	//	return errors.Wrap(err, "Could not subscribe")
	//}
	//go func() {
	//	for msg := range sub {
	//		po := msg.GetOnePODF(XBOS_WAL_PONUM)
	//		if po == nil {
	//			fmt.Println("no valid ponum")
	//			continue
	//		}
	//		msgpo, err := bw2.LoadMsgPackPayloadObject(XBOS_WAL_PONUM, po.GetContents())
	//		if err != nil {
	//			fmt.Println("cannot load msgpack", err)
	//			return
	//		}
	//		var walReq XBOSWALRequest
	//		if err := msgpo.ValueInto(&walReq); err != nil {
	//			fmt.Println("cannot parse msgpack", err)
	//			return
	//		}
	//		//TODO: add uri
	//		ret, err := exec.wal.readUncommitted("", walReq.Seqno, walReq.Batch)
	//		//readUncommitted(msg)
	//	}
	//}()

	select {}

	return nil
}

func (exec *BW2DriverExecutor) refreshInterfaces() {
	exec.interfaceLock.Lock()
	for _, iface := range exec.d.GetInterfaces() {
		if !iface.IsLive() {
			continue
		}
		fmt.Println("Adding", iface.GetName(), "with name", iface.GetInstance())
		exec.publishLiveness(iface)
		exec.interfaces[iface.GetInstance()] = iface
	}
	exec.interfaceLock.Unlock()
}

func (exec *BW2DriverExecutor) publishSignals(iface Interface) error {
	for _, signalname := range iface.GetSignals() {
		data, err := iface.Read(signalname)
		if err != nil {
			fmt.Println(err)
			continue
		}
		// TODO: buffer this
		// TODO: publish it
		publishURI := fmt.Sprintf("%s/s.%s/%s/%s/signal/%s",
			exec.baseURI,
			exec.d.GetName(),
			iface.GetInstance(),
			iface.GetName(),
			signalname,
		)
		datamp := data.SerializeMsgpack()
		hash, err := exec.wal.add(publishURI, datamp)
		if err != nil {
			fmt.Println("err wal add", err)
			continue
		}

		po, err := bw2.LoadMsgPackPayloadObjectPO(data.GetPONum(), datamp)
		if err != nil {
			fmt.Println("err make po", err)
			continue
		}

		exec.cl.Lock()
		err = exec.client.Publish(&bw2.PublishParams{
			URI:            publishURI,
			Persist:        true,
			PayloadObjects: []bw2.PayloadObject{po},
		})
		exec.cl.Unlock()
		if err != nil {
			fmt.Println("err publishing", err)
			continue
		}

		uncommitted, err := exec.wal.uncommitted(publishURI)
		if err != nil {
			fmt.Println(err)
			continue
		}
		fmt.Println("uncommitted (", len(uncommitted), ")")
		//for i, b := range uncommitted {
		//	fmt.Println(" >", i, len(b))
		//}

		fmt.Println(publishURI, data, base64.URLEncoding.EncodeToString(hash))
	}
	return nil
}

func (exec *BW2DriverExecutor) publishLiveness(iface Interface) error {
	exec.cl.Lock()
	defer exec.cl.Unlock()
	uri := fmt.Sprintf("%s/s.%s/%s/%s",
		exec.baseURI,
		exec.d.GetName(),
		iface.GetInstance(),
		iface.GetName(),
	)
	return exec.client.SetMetadata(uri, "lastalive", time.Now().Format(time.RFC3339Nano))
}

// For reading from each of the interfaces, we can just
