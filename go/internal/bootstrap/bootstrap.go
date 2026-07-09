package bootstrap

import (
	"fmt"
	"os/exec"

	"github.com/mistromy/Nirupama/internal/utils"
)

var RunAndLog = utils.RunAndLog

func Bootstrap() {
	fmt.Println("Is first start?")
	fmt.Println(isFirstStart())
	if isFirstStart() {
		setupEnvironment()
		utils.CheckPaths() // set Pip and Python paths
		installBot()
	}
}

func setupEnvironment() {
	checkEnvironment() // check for git, python, pip, conda, and package manager
	fmt.Println("Environment check complete.")

	if Info.GitExists == false { // install git if doesnt exist
		fmt.Println("Git is not installed")
		if utils.AskYesNo("Do you want to install Git?") {
			installGit()
		}
	}

	if utils.IsVersionAtLeast(Info.PythonVersion, "3.10.0") == false {
		fmt.Println("Python Version too old.\nMust be at least 3.10.0")
		if Info.CondaExists == true {
			exec.Command("conda", "create", "-y", "-p", BotEnvDir, "python=3.10").Run()
		} else {
			fmt.Println("Conda is not installed")
			if utils.AskYesNo("Do you want to install Conda?") {
				installCondaFlow()
			}
		}
	} else {
		RunAndLog("python3", "-m", "venv", "./.venv")
		RunAndLog(utils.Pip, "install", "--upgrade", "pip")
	}
}

func installBot() {
	installRepo()
	RunAndLog(utils.Pip, "install", "-r", "requirements.txt")

}
