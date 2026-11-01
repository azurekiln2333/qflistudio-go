//go:build cgo

package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"encoding/json"
	"fmt"
)

type goSourceRequest struct {
	FilePath *string `json:"filePath"`
	Source   *string `json:"source"`
}

// analysisJSON owns the only untyped request boundary. Both exported functions
// return C-allocated JSON; callers release it with the existing QfliGoFree.
func analysisJSON(requestJSON string, formatSource bool) (encoded string) {
	defer func() {
		if value := recover(); value != nil {
			payload, _ := json.Marshal(map[string]any{
				"schemaVersion": goAnalysisSchemaVersion,
				"error":         fmt.Sprintf("Go source analysis failed: %v", value),
			})
			encoded = string(payload)
		}
	}()
	var request goSourceRequest
	err := json.Unmarshal([]byte(requestJSON), &request)
	var result goSourceAnalysis
	if err != nil || request.FilePath == nil || request.Source == nil || *request.FilePath == "" {
		result, _ = newGoSourceAnalysis("", "")
		result.Error = "Invalid Go source request: filePath and source strings are required"
	} else if formatSource {
		result = formatGoSource(*request.FilePath, *request.Source)
	} else {
		result = analyzeGoSource(*request.FilePath, *request.Source)
	}
	payload, err := json.Marshal(result)
	if err != nil {
		return `{"schemaVersion":1,"error":"Unable to encode Go source result"}`
	}
	return string(payload)
}

//export QfliGoAnalyze
func QfliGoAnalyze(requestJSON *C.char) *C.char {
	return C.CString(analysisJSON(C.GoString(requestJSON), false))
}

//export QfliGoFormat
func QfliGoFormat(requestJSON *C.char) *C.char {
	return C.CString(analysisJSON(C.GoString(requestJSON), true))
}
