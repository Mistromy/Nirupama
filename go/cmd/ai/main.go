package main

import (
	"time"

	"charm.land/log/v2"
	"github.com/mistromy/Nirupama/internal/llmabstraction"
)

func main() {
	log.SetLevel(log.DebugLevel)
	log.SetReportCaller(true)

	request := llmabstraction.OutRequest{
		Messages: llmabstraction.Message{
			Role:    "user",
			Content: "Testing",
		},
		SysPrompt: "",
		Timestamp: time.Time{},
		Model:     llmabstraction.MODEL,
	}
	llmabstraction.OpenAI(request)

}
