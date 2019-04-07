package driver

import (
	"github.com/pkg/errors"
)

var ErrUnknownSignal = errors.New("Unknown signal")
var ErrUnknownSlot = errors.New("Unknown slot")
