package main

import (
	"charm.land/log/v2"
)

func main() {
	log.SetLevel(log.DebugLevel)
	log.SetReportCaller(true)

	err := Init()
	if err != nil {
		log.Fatal("Harness Init", "error", err)
		return
	}

}
