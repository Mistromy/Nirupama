package main

import (
	"fmt"
	"os/exec"

	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/bot"
	"github.com/mistromy/Nirupama/internal/utils"
)

func main() {
	fmt.Println("Is first start?")
	fmt.Println(bootstrap.IsFirstStart())

	if bootstrap.IsFirstStart() {
		bootstrap.CheckEnvironment()
		if bootstrap.Info.GitExists == false {
			fmt.Println("Git is not installed")
			if utils.AskYesNo("Do you want to install Git?") {
				bootstrap.InstallGit()
			}
		}
		if utils.IsVersionAtLeast(bootstrap.Info.PythonVersion, "3.10.0") == false {
			fmt.Println("Python Version too old.\nMust be at least 3.10.0")
			if bootstrap.Info.CondaExists == true {
				exec.Command("conda", "create", "-y", "-p", bootstrap.BotEnvDir, "python=3.10").Run()
			} else {
				fmt.Println("Conda is not installed")
				if utils.AskYesNo("Do you want to install Conda?") {
					bootstrap.InstallCondaFlow()
				}
			}
		} else {
			exec.Command("python3", "-m", "venv", "./.venv").Run()
		}
	}

	cmd := bot.Start()
	cmd.Start()
}
