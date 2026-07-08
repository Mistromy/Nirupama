package main

import (
	"fmt"

	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/bot"
)

func main() {
	firstStart := bootstrap.IsFirstStart() // Check if this is the first start of the application. If so, print a welcome message and exit.

	fmt.Println(firstStart)
	if firstStart {

	}
	cmd := bot.Start()
	cmd.Start()
}
