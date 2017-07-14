package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"os"
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
		"{{ end }}\n"

	t := template.Must(template.New("page").Parse(page_template))
	input := map[string]interface{}{
		"Name":        name,
		"Interface":   i.Interface,
		"Description": i.Description,
		"Ponum":       i.Ponum,
		"Signals":     i.Signals,
		"Slots":       i.Slots,
		"Properties":  i.Properties,
	}
	if err := t.Execute(os.Stdout, input); err != nil {
		log.Fatal(err)
	}
	return nil
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
