package driver

type Interface interface {
	// returns name of interface
	GetName() string
	// returns name of instance
	GetInstance() string
	// get names of signals offered by this interface
	GetSignals() []string
	// read signals
	Read(signal string) (MsgpackSerializable, error)
	// write to driver synchronously
	Write(slot string, inp []byte) error
	// returns true if this interface is still alive
	IsLive() bool
}
