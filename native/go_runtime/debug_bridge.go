//go:build cgo

package main

/*
#include <stdlib.h>
*/
import "C"

import "encoding/json"

func encodeDebugResponse(response debugResponse) *C.char {
	encoded, err := json.Marshal(response)
	if err != nil {
		return C.CString(`{"ok":false,"state":"unavailable","error":"unable to encode debug result"}`)
	}
	return C.CString(string(encoded))
}

//export QfliGoDebugStart
func QfliGoDebugStart(id C.ulonglong, request *C.char) *C.char {
	var decoded debugRequest
	if err := json.Unmarshal([]byte(C.GoString(request)), &decoded); err != nil {
		return encodeDebugResponse(debugFailure(uint64(id), err))
	}
	return encodeDebugResponse(startGoDebug(uint64(id), decoded))
}

//export QfliGoDebugPoll
func QfliGoDebugPoll(id, after C.ulonglong) *C.char {
	return encodeDebugResponse(pollGoDebug(uint64(id), uint64(after)))
}

//export QfliGoDebugCommand
func QfliGoDebugCommand(id C.ulonglong, request *C.char) *C.char {
	var decoded debugCommandRequest
	if err := json.Unmarshal([]byte(C.GoString(request)), &decoded); err != nil {
		return encodeDebugResponse(debugFailure(uint64(id), err))
	}
	return encodeDebugResponse(commandGoDebug(uint64(id), decoded))
}

//export QfliGoDebugClose
func QfliGoDebugClose(id C.ulonglong) *C.char { return encodeDebugResponse(closeGoDebug(uint64(id))) }
