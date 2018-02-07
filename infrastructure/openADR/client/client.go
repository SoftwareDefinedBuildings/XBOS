/*
 * go build -o drclient
 * ./drclient
 *
 * This is a test client that simulates the price signal from Siemens
 * it reads the signal from an XML file and sends it as a POST request
 * to a server that parses and publishes the signal securely over BOSSWAVE
 */
package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"
)

// HTTP Client
var client = &http.Client{Timeout: 10 * time.Second}

// function to load a PRICE SIGNAL XML file
func loadXMLFile(path string) io.Reader {
	//open file
	xmlFile, err := os.Open(path)
	if err != nil {
		log.Fatal("Error opening file:", err)
		return nil
	}
	return xmlFile
}

// function to send a POST request to a server
func sendPOSTRequest(url string, header string, stream io.Reader) {
	// check that
	if stream == nil || header == "" {
		log.Fatal("Error empty stream or request header")
		return
	}

	// POST the request
	resp, err := client.Post(url, header, stream)
	if err != nil {
		log.Fatal(err)
		return
	}
	defer resp.Body.Close()

	// print the response
	fmt.Println(resp)
}

func main() {
	sendPOSTRequest("http://localhost:8080/", "text/xml", loadXMLFile("price.json"))
}
