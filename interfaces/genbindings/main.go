package main

import (
	//"bytes"
	"fmt"
	//"go/format"
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
	//page_template := "## XBOS {{.Name}}\n\n" +
	//	"**Interface**: {{.Interface}}\n\n" +
	//	"**Description**: {{.Description}}\n\n" +
	//	"**PONUM**: {{.Ponum}}\n\n" +
	//	"### Properties\n\n" +
	//	"| **Name** | **Type** | **Description** | **Units** | **Required** |\n" +
	//	"| :------- | :------- | :-------------- | :-------- | :----------- |\n" +
	//	"{{ range $name, $info := .Properties }}| {{ $name }} | {{ $info.type }} | {{ $info.description }} | {{ $info.units }} | {{ $info.required }} |\n" +
	//	"{{ end }}\n\n" +
	//	"### Signals\n" +
	//	"{{ range $name, $list := .Signals }}- `{{ $name }}`:\n" +
	//	"    {{ range $item := $list }}- `{{ $item }}`\n" +
	//	"    {{ end }}\n" +
	//	"{{ end }}\n\n" +
	//	"### Slots\n" +
	//	"{{ range $name, $list := .Slots }}- `{{ $name }}`:\n" +
	//	"    {{ range $item := $list }}- `{{ $item }}`\n" +
	//	"    {{ end }}\n" +
	//	"{{ end }}\n\n" +
	//	"### Interfacing in Go\n\n"

	//	go_template := `package main
	//import (
	//    bw2 "gopkg.in/immesys/bw2bind.v5"
	//    "fmt"
	//)
	//
	//func main() {
	//    client := bw2.ConnectOrExit("")
	//    client.OverrideAutoChainTo(true)
	//    client.SetEntityFromEnvironOrExit()
	//
	//    base_uri := "{{.Name}} uri goes here ending in {{.Interface}}"
	//
	//    // subscribe
	//    type signal struct {
	//        {{ range $name := index .Signals "info" }}
	//            {{ with $type := index $.Properties $name "type" }}{{ call $.title $name }} {{ call $.gettype $type }}{{ end }} {{ call $.gettag $name }} {{ end }}
	//    }
	//    c, err := client.Subscribe(&bw2.SubscribeParams{
	//        URI: base_uri+"/signal/info",
	//    })
	//    if err != nil {
	//        panic(err)
	//    }
	//
	//    for msg := range c {
	//        var current_state signal
	//        po := msg.GetOnePODF("{{ .Ponum }}/32")
	//        err := po.(bw2.MsgPackPayloadObject).ValueInto(&current_state)
	//        if err != nil {
	//            fmt.Println(err)
	//        } else {
	//            fmt.Println(current_state)
	//        }
	//    }
	//}
	//    `

	python_template := `import time
import msgpack

from bw2python.bwtypes import PayloadObject
from bw2python.client import Client
from xbos.util import read_self_timeout

class {{.Name}}(object):
    def __init__(self, client=None, uri=None):
        self.client = client
        self._uri = uri.rstrip('/')
        self._state = {
{{ range $name, $info := .Properties }}         "{{ $name }}": None,
{{ end }}        }
        def _handle(msg):
            for po in msg.payload_objects:
                if po.type_dotted == {{ call .pythondf .Ponum }}:
                    data = msgpack.unpackb(po.content)
                    for k,v in data.items():
                        self._state[k] = v
        # check liveness
        liveness_uri = "{0}/!meta/lastalive".format(uri)
        res = self.client.query(liveness_uri)
        if len(res) == 0:
            raise Exception("No liveness message found at {0}. Is this URI correct?".format(liveness_uri))
        alive = msgpack.unpackb(res[0].payload_objects[0].content)
        ts = alive['ts'] / 1e9
        if time.time() - ts > 30:
            raise Exception("{0} more than 30sec old. Is this URI current?".format(liveness_uri))
        print "Got {{.Name}} at {0} last alive {1}".format(uri, alive['val'])

        self.client.subscribe("{0}/signal/info".format(uri), _handle)

{{ range $name, $info := .Properties }}{{ if ne $name "time" }}    @property
    def {{$name}}(self, timeout=30):
        return read_self_timeout(self, '{{$name}}', timeout)

{{end}}{{end}}
    def write(self, state):
        po = PayloadObject({{ call .pythondf .Ponum }}, None, msgpack.packb(state))
        self.client.publish('{0}/slot/state'.format(self._uri),payload_objects=(po,))

{{ range $idx, $name := index .Slots "state" }}    def set_{{$name}}(self, value):
        self.write({'{{$name}}': value})

{{end}}`

	//t := template.Must(template.New("page").Parse(page_template))
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
	//if err := t.Execute(os.Stdout, input); err != nil {
	//	log.Fatal(err)
	//}
	//gobuf := bytes.NewBuffer(nil)
	//t2 := template.Must(template.New("go").Parse(go_template))
	//if err := t2.Execute(gobuf, input); err != nil {
	//	log.Fatal(err)
	//}
	//output, err := format.Source(gobuf.Bytes())
	//if err != nil {
	//	log.Fatal(err)
	//}
	//fmt.Println("```go")
	//fmt.Print(string(output))
	//fmt.Println("```")

	//fmt.Println("### Interfacing in Python\n")
	//fmt.Println("```python")
	t3 := template.Must(template.New("python").Parse(python_template))
	if err := t3.Execute(os.Stdout, input); err != nil {
		log.Fatal(err)
	}
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
