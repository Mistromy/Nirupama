package main

import (
	"charm.land/log/v2"
	"github.com/mistromy/Nirupama/internal/llmabstraction"
)

func Init() error {
	turn()
	return nil
}

func turn() {
	response := llmabstraction.Call("Mist(859371145076932619): testing")
	log.Info(response.Message.Content)
}
