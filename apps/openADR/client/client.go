/*
 go build -o drclient
 ./drclient

 This is a test client that simulates the price signal from Siemens
 it reads the signal from a file containing a JSON wrapped XML message
 and sends it as a POST request to a server that parses and publishes
 the signal securely over BOSSWAVE
*/

package main

import (
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"time"
)

// HTTP Client
var client = &http.Client{Timeout: 10 * time.Second}

// loadFile loads a PRICE SIGNAL from a file
func loadFile(p string) io.Reader {
	f, err := os.Open(p)
	if err != nil {
		log.Fatal("Error opening file:", err)
		return nil
	}
	return f
}

// sendPOSTRequest sends a POST request to a server
func sendPOSTRequest(u string, h string, s io.Reader) {
	if s == nil || h == "" {
		log.Fatal(errors.New("Error empty stream or request header"))
		return
	}
	r, err := client.Post(u, h, s)
	if err != nil {
		log.Fatal(err)
		return
	}
	defer r.Body.Close()
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		log.Fatal("Error: Could not read request body:", err)
		return
	}
	fmt.Println(r)
	fmt.Println(string(body))
}

func main() {
	sendPOSTRequest("http://localhost:9673/", "application/json", loadFile("signal.json"))
}
