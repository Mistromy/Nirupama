package main

import (
	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/bot"
)

var systemSpecifics bootstrap.SystemSpecific = bootstrap.GetSystemSpecific()

func main() {
	bot.FindRoot()

	// tui.StartDashboard()
	// bootstrap.CheckExternalDependencies()
	// bot.GitUpdate()
	// bot.InstallDependencies(systemSpecifics)
	// bot.Start() //TODO: Capture logs, and read the close signal to gracefully shutdown the bot
}
