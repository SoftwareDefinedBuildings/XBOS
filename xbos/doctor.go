package main

import (
	"fmt"
	"math/big"
	"net"
	"os"
	"os/exec"

	"github.com/fatih/color"
	"github.com/immesys/bw2bind"
	"github.com/urfave/cli"
)

var (
	red    func(string, ...interface{})
	green  func(string, ...interface{})
	yellow func(string, ...interface{})
	cyan   func(string, ...interface{})
)

func init() {
	_red := color.New(color.FgRed)
	_red.Add(color.Bold)
	_green := color.New(color.FgGreen)
	_green.Add(color.Bold)
	_yellow := color.New(color.FgYellow)
	_yellow.Add(color.Bold)
	_cyan := color.New(color.FgCyan)
	_cyan.Add(color.Bold)
	red = _red.PrintfFunc()
	green = _green.PrintfFunc()
	yellow = _yellow.PrintfFunc()
	cyan = _cyan.PrintfFunc()
	bw2bind.SilenceLog()
}

func actionDoctor(c *cli.Context) error {
	// CHECK 1: check internet access by dialing some dns servers
	// check IPv4 connectivity by attempting to open a TCP connection
	// with the ucberkeley designated router
	network_ok := true
	cyan("▶ Checking network connectivity...\n")
	ipv4addr, err := net.ResolveTCPAddr("tcp4", "52.9.178.236:4514")
	if err != nil {
		red("✖ Could not resolve address 52.9.178.236:4514 (%s)\n", err)
		network_ok = false
	}
	conn, err := net.DialTCP("tcp4", nil, ipv4addr)
	if err != nil {
		red("✖ Could not connect to 52.9.178.236:4514 (%s)\n", err)
		network_ok = false
	}
	if network_ok {
		green("✔ Network connectivity looks ok!\n")
		defer conn.Close()
	} else {
		red("✖ Network connectivity needs attention. Make sure you have an internet connection\n")
	}

	fmt.Println()

	// CHECK 2: check have access to pundat, bw2, spawnctl commands
	cli_ok := true
	cyan("▶ Checking command line tools...\n")
	tools := []string{"bw2", "pundat", "spawnctl", "xbos"}
	for _, tool := range tools {
		path, err := exec.LookPath(tool)
		if err != nil {
			red("✖ Could not find tool %s in $PATH (%s)\n", tool, err)
			cli_ok = false
		} else {
			green("✔ Found tool %s at %s\n", tool, path)
		}
	}
	if cli_ok {
		green("✔ Command line tools look ok!\n")
	} else {
		red("✖ Command line tools needs attention. Make sure you have pundat, bw2, spawnctl and xbos installed and in your PATH\n")
	}

	fmt.Println()

	// CHECK 3: check env vars: default entity, bw2 agent, default bankroll, default contact
	// TODO: suggest default values for these
	// TODO: maybe have a help doc on each item?
	// TODO: check that the entities are live and well
	cyan("▶ Checking bosswave state...\n")
	envvars_ok := true
	envvars := []struct {
		varname  string
		isEntity bool
		help     string
	}{
		{
			"BW2_AGENT",
			false,
			"The IP:Port of the agent we connect to. Default 127.0.0.1:28589, typically 172.17.0.1:28589 if its in a container",
		},
		{
			"BW2_DEFAULT_ENTITY",
			true,
			"The BW2 entity we perform actions as. To create, run 'bw2 mkentity'",
		},
		{
			"BW2_DEFAULT_BANKROLL",
			true,
			"The BW2 entity we use to pay for things. To create, run 'bw2 mkentity'. Can also be the same entity as BW2_DEFAULT_ENTITY",
		},
		{
			"BW2_DEFAULT_CONTACT",
			false,
			"The real-world identity or contact for this entity. Typically name+email",
		},
		{
			"BW2_DEFAULT_EXPIRY",
			false,
			"The default expiry for DOTs and entities. Recommend '10y'",
		},
	}
	for _, ev := range envvars {
		var value string
		var val *string
		if val = checkEnvDefined(ev.varname); val == nil {
			envvars_ok = false
			continue
		}
		value = *val
		if ev.isEntity {
			if !fileExists(value) {
				red("✖ Value for %s (%s) does not exist. Expected valid entity file", ev.varname, value)
			}
			vk, entity, err := readEntityFile(value)
			if err != nil {
				envvars_ok = false
				red(err.Error())
				continue
			}
			if entity.IsExpired() {
				if ev.varname == "BW2_DEFAULT_BANKROLL" {
					yellow("✅ Entity (%s) with VK %s is expired. For Bankroll this is ok\n", ev.varname, vk)
				} else {
					red("✖ Entity (%s) with VK %s is expired!\n", ev.varname, vk)
					envvars_ok = false
				}
				continue
			}
		}
	}

	if envvars_ok {
		green("✔ Environment vars look ok!\n")
	} else {
		red("✖ Environment vars need attention. Make sure you have $BW2_DEFAULT_ENTITY, $BW2_AGENT, and $BW2_DEFAULT_BANKROLL all set and that $BW2_DEFAULT_ENTITY and $BW2_DEFAULT_BANKROLL point to valid BW2 entities\n")
	}

	var bw_ok = true
	// check chain is up to date
	client, err := bw2bind.Connect("")
	if err != nil {
		red("✖ Could not connect to local agent (%s)", err)
		bw_ok = false
		return err
	}
	bcip, err := client.GetBCInteractionParams()
	if err != nil {
		red("✖ Could not get current blockchain state (%s)", err)
		bw_ok = false
		return err
	}
	/*
	   type CurrentBCIP struct {
	        Confirmations int64
	        Timeout       int64
	        Maxage        int64
	        CurrentAge    time.Duration
	        CurrentBlock  uint64
	        Peers         int64
	        HighestBlock  int64
	        Difficulty    int64
	   }
	*/
	if int64(bcip.CurrentBlock) < bcip.HighestBlock-1 { // fudge factor of 1 block
		red("✖ Chain is not caught up. At block %d but current is %d. If you have peers, this should go away\n", bcip.CurrentBlock, bcip.HighestBlock)
		bw_ok = false
	} else {
		green("✔ Caught up on the blockchain\n")
	}

	// check chain has peers
	if bcip.Peers == 0 {
		red("✖ You do not have peers! Check if you have an internet connection\n")
		bw_ok = false
	} else {
		green("✔ Have %d peers\n", bcip.Peers)
	}

	// check bankroll has money
	val := checkEnvDefined("BW2_DEFAULT_BANKROLL")
	if val == nil {
		red("✖ Cannot check bankroll balance because $BW2_DEFAULT_BANKROLL is not defined\n")
		bw_ok = false
		return nil
	}
	_, err = client.SetEntityFile(*val)
	if err != nil {
		red("✖ Can't use $BW2_DEFAULT_BANKROLL (%s)\n", err)
		bw_ok = false
		return nil
	}
	accounts, err := client.EntityBalances()
	if err != nil {
		red("✖ Cannot fetch bankroll balances (%s)\n", err)
		bw_ok = false
		return nil
	}
	has_some_money := false
	max_balance := int64(0)
	for _, acc := range accounts {
		balance := weiToCurrency(acc.Int)
		if balance > 0 {
			has_some_money = true
		}
		if balance > max_balance {
			max_balance = balance
		}
	}
	if max_balance > 100 {
		green("✔ $BW2_DEFAULT_BANKROLL has %d Ether in at least one account!\n", max_balance)
	} else if has_some_money {
		yellow("✅ $BW2_DEFAULT_BANKROLL has %d Ether in at least one account, but is running low\n", max_balance)
	} else {
		red("✖ $BW2_DEFAULT_BANKROLL has no funds\n")
		bw_ok = false
	}

	// check disk space
	disk := diskUsage()
	if disk < 10000 {
		red("✖ Only have %f MB left on disk\n", disk)
		bw_ok = false
	} else {
		green("✔ Have %f MB left on disk. Should be good\n", disk)
	}

	if bw_ok {
		green("✔ BOSSWAVE state looks ok!\n")
	} else {
		red("✖ BOSSWAVE state needs attention\n")
	}

	// TODO: check software up to date

	return nil
}

// checks if the given environment variable exists. If it does, returns a pointer to
// the value, else nil if its not defined
func checkEnvDefined(name string) *string {
	value, found := os.LookupEnv(name)
	if !found {
		red("✖ Could not find entry for %s\n", name)
		return nil
	} else if value == "" {
		red("✖ Found entry for %s but it was empty\n", name)
		return nil
	} else {
		green("✔ %s = %s\n", name, value)
		return &value
	}
}

func weiToCurrency(w *big.Int) int64 {
	f := big.NewFloat(0)
	f.SetInt(w)
	f = f.Quo(f, big.NewFloat(1000000000000000000.0))
	v, _ := f.Int64()
	return v
}
