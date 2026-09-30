//go:build cgo

package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"context"
	"encoding/json"
	"sync"
	"unsafe"
)

var runs = struct {
	sync.Mutex
	active    map[uint64]context.CancelFunc
	cancelled map[uint64]bool
}{active: make(map[uint64]context.CancelFunc), cancelled: make(map[uint64]bool)}

//export QfliGoRun
func QfliGoRun(id C.ulonglong, projectPath, entryFile *C.char) *C.char {
	ctx, cancel := context.WithCancel(context.Background())
	runID := uint64(id)
	runs.Lock()
	runs.active[runID] = cancel
	if runs.cancelled[runID] {
		cancel()
	}
	delete(runs.cancelled, runID)
	runs.Unlock()

	result := runGoWithContext(ctx, C.GoString(projectPath), C.GoString(entryFile))
	runs.Lock()
	delete(runs.active, runID)
	runs.Unlock()
	cancel()
	encoded, err := json.Marshal(result)
	if err != nil {
		return C.CString(`{"stdout":"","stderr":"unable to encode Go result","exitCode":127}`)
	}
	return C.CString(string(encoded))
}

//export QfliGoCancel
func QfliGoCancel(id C.ulonglong) {
	runID := uint64(id)
	runs.Lock()
	if cancel, ok := runs.active[runID]; ok {
		cancel()
	} else {
		runs.cancelled[runID] = true
	}
	runs.Unlock()
}

//export QfliGoFree
func QfliGoFree(value *C.char) {
	C.free(unsafe.Pointer(value))
}
