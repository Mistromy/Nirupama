package bootstrap

import (
	"os"

	"github.com/mistromy/Nirupama/internal/utils"
)

var RunAndLog = utils.RunAndLog
var RunAsUserAndLog = utils.RunAsUserAndLog

func Bootstrap() {
	utils.CyanLog("Is first start?")
	utils.CyanLog("%t", isFirstStart())
	if isFirstStart() {
		setupEnvironment()
		utils.CheckPaths() // set Pip and Python paths
		installBot()
		os.Exit(0)
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
		} else {
			utils.CyanLog("Git is required to continue. Exiting.")
			os.Exit(1)
		}
	}

	if utils.IsVersionAtLeast(Info.PythonVersion, "3.10.0") == false {
		utils.CyanLog("Python Version too old.\nMust be at least 3.10.0")
		if Info.CondaExists == true {
			RunAsUserAndLog("conda", "create", "-y", "-p", BotEnvDir, "python=3.10")
		} else {
			utils.CyanLog("Conda is not installed")
			if utils.AskYesNo("Do you want to install Conda?") {
				installCondaFlow()
			} else {
				utils.CyanLog("Conda is required to continue. Exiting.")
				os.Exit(1)
			}
		}
	} else {
		RunAsUserAndLog("python3", "-m", "venv", "./.venv")
		RunAsUserAndLog(utils.Pip, "install", "--upgrade", "pip")
	}
}

func installBot() {
	installRepo()
	RunAsUserAndLog(utils.Pip, "install", "-r", "requirements.txt")
}
