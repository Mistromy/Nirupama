package main

import (
	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/bot"
)

func main() {
	bootstrap.Bootstrap()

	cmd := bot.Start()
	cmd.Start()
}
