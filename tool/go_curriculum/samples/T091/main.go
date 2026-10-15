// T091 JSON 三：流式 Decoder/Encoder 与未知字段。
//
// json.Decoder 可以连续解码一个流中的多个 JSON 值（如 NDJSON），
// 比 Unmarshal 更适合逐步读取；Decoder.DisallowUnknownFields 会让
// 未知字段报错，便于严格校验。
// 本示例演示：连续解码多个对象、忽略未知字段（默认行为）。
package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

// Event 是流中的一个事件对象。
type Event struct {
	Type string `json:"type"`
	Code int    `json:"code"`
}

func main() {
	// 一个"流"里包含三个 JSON 对象，其中第二个还有未知字段 extra。
	stream := `{"type":"start","code":1}
{"type":"tick","code":2,"extra":"ignored"}
{"type":"stop","code":3}`

	dec := json.NewDecoder(strings.NewReader(stream))
	count := 0
	for dec.More() {
		var e Event
		// 默认忽略未知字段，因此第二行能成功解码。
		if err := dec.Decode(&e); err != nil {
			panic(err)
		}
		count++
		fmt.Printf("event %d: type=%s code=%d\n", count, e.Type, e.Code)
	}
	fmt.Println("decoded events:", count)

	// 严格模式：未知字段会报错。
	strict := json.NewDecoder(strings.NewReader(`{"type":"x","code":9,"bogus":true}`))
	strict.DisallowUnknownFields()
	var e Event
	err := strict.Decode(&e)
	fmt.Println("strict decode rejected unknown field:", err != nil)
}
