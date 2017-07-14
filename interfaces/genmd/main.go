package main

import (
	"bytes"
	"fmt"
	"go/format"
	"io/ioutil"
	"log"
	"os"
	"strings"
	"text/template"

	"gopkg.in/yaml.v2"
)

// Take a YAML file (swagger-like) and generate a markdown page
//
// Example
//
//
//     Light:
//         description: Standard XBOS lighting interface
//         ponum: 2.1.1.1
//         interface: i.xbos.light
//         signals:
//             - info:
//                 - state
//                 - brightness
//                 - time
//         slots:
//             - state:
//                 - state
//                 - brightness
//         properties:
//             state:
//                 type: boolean
//                 description: Whether or not the light is on
//                 required: true
//             brightness:
//                 type: integer
//                 maximum: 100
//                 minimum: 0
//                 description: Current brightness of the light; 100 is maximum brightness
//                 required: false
//             time:
//                 type: integer
//                 description: nanoseconds since the Unix epoch
//                 required: false

type Interface struct {
	Description string
	Ponum       string
	Interface   string
	Signals     map[string][]string
	Slots       map[string][]string
	Properties  map[string]map[string]interface{}
}

func (i Interface) Markdown(name string) []byte {
	page_template := "## XBOS {{.Name}}\n\n" +
		"**Interface**: {{.Interface}}\n\n" +
		"**Description**: {{.Description}}\n\n" +
		"**PONUM**: {{.Ponum}}\n\n" +
		"### Properties\n\n" +
		"| **Name** | **Type** | **Description** | **Units** | **Required** |\n" +
		"| :------- | :------- | :-------------- | :-------- | :----------- |\n" +
		"{{ range $name, $info := .Properties }}| {{ $name }} | {{ $info.type }} | {{ $info.description }} | {{ $info.units }} | {{ $info.required }} |\n" +
		"{{ end }}\n\n" +
		"### Signals\n" +
		"{{ range $name, $list := .Signals }}- `{{ $name }}`:\n" +
		"    {{ range $item := $list }}- `{{ $item }}`\n" +
		"    {{ end }}\n" +
		"{{ end }}\n\n" +
		"### Slots\n" +
		"{{ range $name, $list := .Slots }}- `{{ $name }}`:\n" +
		"    {{ range $item := $list }}- `{{ $item }}`\n" +
		"    {{ end }}\n" +
		"{{ end }}\n\n" +
		"### Interfacing in Go\n\n"

	go_template := `package main
import (
    bw2 "gopkg.in/immesys/bw2bind.v5"
    "fmt"
)

func main() {
    client := bw2.ConnectOrExit("")
    client.OverrideAutoChainTo(true)
    client.SetEntityFromEnvironOrExit()

    base_uri := "{{.Name}} uri goes here ending in {{.Interface}}"

    // subscribe
    type signal struct {
        {{ range $name := index .Signals "info" }}
            {{ with $type := index $.Properties $name "type" }}{{ call $.title $name }} {{ call $.gettype $type }}{{ end }} {{ call $.gettag $name }} {{ end }}
    }
    c, err := client.Subscribe(&bw2.SubscribeParams{
        URI: base_uri+"/signal/info",
    })
    if err != nil {
        panic(err)
    }

    for msg := range c {
        var current_state signal
        po := msg.GetOnePODF("{{ .Ponum }}/32")
        err := po.(bw2.MsgPackPayloadObject).ValueInto(&current_state)
        if err != nil {
            fmt.Println(err)
        } else {
            fmt.Println(current_state)
        }
    }
}
    `

	python_template := `
import time
import msgpack

from bw2python.bwtypes import PayloadObject
from bw2python.client import Client

bw_client = Client()
bw_client.setEntityFromEnviron()
bw_client.overrideAutoChainTo(True)

def onMessage(bw_message):
  for po in bw_message.payload_objects:
    if po.type_dotted == {{ call .pythondf .Ponum }}:
      print msgpack.unpackb(po.content)

bw_client.subscribe("{{.Name}} uri ending in {{.Interface}}/signal/info", onMessage)

print "Subscribing. Ctrl-C to quit."
while True:
  time.sleep(10000)
`

	t := template.Must(template.New("page").Parse(page_template))
	input := map[string]interface{}{
		"Name":        name,
		"Interface":   i.Interface,
		"Description": i.Description,
		"Ponum":       i.Ponum,
		"Signals":     i.Signals,
		"Slots":       i.Slots,
		"Properties":  i.Properties,
		"gettype":     gettype,
		"title":       strings.Title,
		"gettag":      gettag,
		"pythondf":    pythondf,
	}
	if err := t.Execute(os.Stdout, input); err != nil {
		log.Fatal(err)
	}
	gobuf := bytes.NewBuffer(nil)
	t2 := template.Must(template.New("go").Parse(go_template))
	if err := t2.Execute(gobuf, input); err != nil {
		log.Fatal(err)
	}
	output, err := format.Source(gobuf.Bytes())
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("```go")
	fmt.Print(string(output))
	fmt.Println("```")

	fmt.Println("### Interfacing in Python\n")
	fmt.Println("```python")
	t3 := template.Must(template.New("python").Parse(python_template))
	if err := t3.Execute(os.Stdout, input); err != nil {
		log.Fatal(err)
	}
	fmt.Println("```")
	return nil
}

func gettype(typ string) string {
	switch typ {
	case "string":
		return "string"
	case "boolean":
		return "bool"
	case "integer":
		return "int64"
	case "double":
		return "float64"
	}
	return typ
}

func gettag(name string) string {
	return fmt.Sprintf("`msgpack:\"%s\"`", name)
}

func pythondf(df string) string {
	return fmt.Sprintf("(%s)", strings.Replace(df, ".", ",", -1))
}

func main() {
	file := os.Args[1]
	bytes, err := ioutil.ReadFile(file)
	if err != nil {
		log.Fatal(err)
	}
	var target = make(map[string]Interface)
	err = yaml.Unmarshal(bytes, target)
	//fmt.Println(bytes)
	if err != nil {
		log.Fatal(err)
	}
	//fmt.Printf("%+v", target)
	fmt.Println()
	for k, v := range target {
		v.Markdown(k)
	}
}
