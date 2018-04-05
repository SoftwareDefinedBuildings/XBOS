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
	exec.client = bw2.ConnectOrExit("")
	exec.client.OverrideAutoChainTo(true)
	exec.client.SetEntityFromEnvironOrExit()
	exec.interfaces = make(map[string]Interface)
	exec.baseURI = params.MustString("base_uri")

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
		hash, err := exec.wal.add(publishURI, []byte{1, 2, 3, 4, 5})
		if err != nil {
			fmt.Println(err)
			continue
		}
		uncommitted, err := exec.wal.uncommitted(publishURI)
		if err != nil {
			fmt.Println(err)
			continue
		}
		for i, b := range uncommitted {
			fmt.Println(" >", i, len(b))
		}

		fmt.Println(publishURI, data, base64.URLEncoding.EncodeToString(hash))
	}
	return nil
}

func (exec *BW2DriverExecutor) publishLiveness(iface Interface) error {
	uri := fmt.Sprintf("%s/s.%s/%s/%s",
		exec.baseURI,
		exec.d.GetName(),
		iface.GetInstance(),
		iface.GetName(),
	)
	return exec.client.SetMetadata(uri, "lastalive", time.Now().Format(time.RFC3339Nano))
}

// For reading from each of the interfaces, we can just
