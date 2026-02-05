package main

import (
	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/bot"
	"github.com/mistromy/Nirupama/internal/tui"
)

var systemSpecifics bootstrap.SystemSpecific = bootstrap.GetSystemSpecific()

func main() {
	tui.StartDashboard()
	bootstrap.CheckExternalDependencies()
	bot.GitUpdate()
	bot.InstallDependencies(systemSpecifics)
	bot.Start()
}
