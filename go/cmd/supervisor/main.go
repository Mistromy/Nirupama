package main

import (
	"fmt"
	"io"
	"log"
	"os/exec"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/bot"
	"github.com/mistromy/Nirupama/internal/tui"
	"github.com/mistromy/Nirupama/internal/utils/paths"
)

var systemSpecifics bootstrap.SystemSpecific = bootstrap.GetSystemSpecific()

func maintest() {
	paths.FindRoot()
	// requirementsPath := paths.GetPath("requirements.txt")
	// 1. Setup the command exactly as you run it
	// NOTE: Change "pip" to "pip3" if you are on Linux/Mac and need to
	cmd := exec.Command("pip", "--version")

	// 2. We need to hijack the output pipes before starting
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		panic(err)
	}

	// Redirect stderr to the same place so we catch everything
	cmd.Stderr = cmd.Stdout

	// 3. Start the process
	fmt.Println("--- STARTING RAW CAPTURE ---")
	if err := cmd.Start(); err != nil {
		panic(err)
	}

	// 4. Read raw bytes directly.
	// Do not use Scanner here, because Scanner automatically removes \r and \n!
	buf := make([]byte, 1024)
	for {
		n, err := stdout.Read(buf)
		if n > 0 {
			chunk := buf[:n]
			// %q is the Go syntax for "Quoted String".
			// It turns invisible chars into visible codes (e.g. it prints '\r' instead of moving the cursor).
			fmt.Printf("%q\n", chunk)
		}
		if err != nil {
			if err == io.EOF {
				break
			}
			panic(err)
		}
	}

	cmd.Wait()
	fmt.Println("--- END CAPTURE ---")
}

func main() {
	log.SetFlags(0) // Remove timestamp from log output for cleaner TUI display

	startFunctions := func(p *tea.Program) { // Other functions to start, to be sent to tui to run in a goroutine.

		paths.FindRoot() // Find the root directory of the project and set it in the paths package. To be used by other packages that need to find a specific file.

		bootstrap.CheckExternalDependencies() // Check existance of git, python and pip. If any of them are missing, print a warning and exit.

		bot.GitUpdate()                          // Update the bot from git.
		bot.InstallDependencies(systemSpecifics) // Install the dependencies from requirements.txt. If it doesn't exist, print a warning and continue.

		cmd := bot.Start() // Start the bot. This will block until the bot process exits.
		if cmd != nil {
			p.Send(tui.BotProcMsg{Cmd: cmd}) // Send the bot process to the TUI so it can be killed on exit.
		}
		if cmd != nil {
			cmd.Wait()
		}

	}

	tui.StartDashboard(startFunctions) // Start the TUI Dashboard and run all the start commands in a goroutine.
}
