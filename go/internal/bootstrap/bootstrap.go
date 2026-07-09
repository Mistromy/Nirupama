package bootstrap

import (
	"os/exec"

	"github.com/mistromy/Nirupama/internal/utils"
)

var RunAndLog = utils.RunAndLog

func Bootstrap() {
	utils.CyanLog("Is first start?")
	utils.CyanLog("%t", isFirstStart())
	if isFirstStart() {
		setupEnvironment()
		utils.CheckPaths() // set Pip and Python paths
		installBot()
	}
}

func setupEnvironment() {
	checkEnvironment() // check for git, python, pip, conda, and package manager
	utils.CyanLog("Environment check complete.")

	utils.RunAndLog("sudo", Info.PackageManager, "update", "-y")

	if Info.GitExists == false { // install git if doesnt exist
		utils.CyanLog("Git is not installed")
		if utils.AskYesNo("Do you want to install Git?") {
			installGit()
		}
	}

	if utils.IsVersionAtLeast(Info.PythonVersion, "3.10.0") == false {
		utils.CyanLog("Python Version too old.\nMust be at least 3.10.0")
		if Info.CondaExists == true {
			exec.Command("conda", "create", "-y", "-p", BotEnvDir, "python=3.10").Run()
		} else {
			utils.CyanLog("Conda is not installed")
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
