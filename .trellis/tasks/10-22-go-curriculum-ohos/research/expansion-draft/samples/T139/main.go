package main

import (
	"encoding/xml"
	"fmt"
)

type Item struct {
	SKU      string `xml:"sku,attr"`
	Quantity int    `xml:"quantity"`
}
type Inventory struct {
	XMLName xml.Name `xml:"inventory"`
	Items   []Item   `xml:"items>item"`
}

func main() {
	input := `<inventory><items><item sku="A"><quantity>1</quantity></item><item sku="B"><quantity>7</quantity></item></items></inventory>`
	var inventory Inventory
	if err := xml.Unmarshal([]byte(input), &inventory); err != nil {
		panic(err)
	}
	changed := 0
	for i := range inventory.Items {
		if inventory.Items[i].Quantity < 5 {
			inventory.Items[i].Quantity = 5
			changed++
		}
	}
	encoded, err := xml.Marshal(inventory)
	if err != nil {
		panic(err)
	}
	var restored Inventory
	if err := xml.Unmarshal(encoded, &restored); err != nil {
		panic(err)
	}
	fmt.Printf("restocked=%d\n", changed)
	fmt.Printf("%s=%d %s=%d\n", restored.Items[0].SKU, restored.Items[0].Quantity, restored.Items[1].SKU, restored.Items[1].Quantity)
	fmt.Printf("roundtrip=%t\n", len(restored.Items) == 2 && restored.Items[0].Quantity == 5 && restored.Items[1].Quantity == 7)
	err = xml.Unmarshal([]byte(`<inventory><items><item sku="C"><quantity>many</quantity></item></items></inventory>`), &restored)
	fmt.Printf("bad-stock=%t\n", err != nil)
}
