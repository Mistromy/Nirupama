package main

import (
	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/bot"
	"github.com/mistromy/Nirupama/internal/tui"
)

var systemspcifics bootstrap.SystemSpecific = bootstrap.GetSystemSpecific()

func main() {
	tui.StartDashboard()
	bootstrap.CheckExternalDependencies()
	bot.GitUpdate()
	bot.InstallDependencies(systemspcifics)
	bot.Start(nil)
}
