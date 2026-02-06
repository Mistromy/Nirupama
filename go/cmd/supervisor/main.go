package main

import (
	"log"

	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/bot"
	"github.com/mistromy/Nirupama/internal/utils/paths"
)

var systemSpecifics bootstrap.SystemSpecific = bootstrap.GetSystemSpecific()

func main() {
	log.SetFlags(0)
	// tui.StartDashboard() // Start the TUI dashboard in a separate goroutine

	paths.FindRoot() // Find the root directory of the project and set it in the paths package. To be used by other packages that need to find a specific file.

	bootstrap.CheckExternalDependencies() // Check existance of git, python and pip. If any of them are missing, print a warning and exit.

	bot.GitUpdate()                          // Update the bot from git.
	bot.InstallDependencies(systemSpecifics) // Install the dependencies from requirements.txt. If it doesn't exist, print a warning and continue.

	bot.Start()
}
