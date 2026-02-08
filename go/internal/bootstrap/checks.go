package bootstrap

import (
	"log"
	"os/exec"
	"runtime"
)

type SystemSpecific struct {
	Pip    string
	Python string
}

func GetSystemSpecific() SystemSpecific {
	var systemSpecificTools SystemSpecific
	if runtime.GOOS == "windows" {
		systemSpecificTools.Pip = "pip"
		systemSpecificTools.Python = "python"
	} else {
		systemSpecificTools.Pip = "pip3"
		systemSpecificTools.Python = "python3"
	}
	return systemSpecificTools
}

func CheckExternalDependencies() []string {
	missing := []string{}
	systemSpecificTools := GetSystemSpecific()

	cmd := exec.Command(systemSpecificTools.Python, "--version")
	cmd.Stdout = log.Writer()
	cmd.Stderr = log.Writer()
	err := cmd.Run()
	if err != nil {
		log.Println("Error checking Python version:", err)
		missing = append(missing, "python")
	}
	cmd = exec.Command(systemSpecificTools.Pip, "--version")
	cmd.Stdout = log.Writer()
	cmd.Stderr = log.Writer()
	err = cmd.Run()
	if err != nil {
		log.Println("Error checking pip version:", err)
		missing = append(missing, "pip")
	}
	cmd = exec.Command("git", "--version")
	cmd.Stdout = log.Writer()
	cmd.Stderr = log.Writer()
	err = cmd.Run()
	if err != nil {
		log.Println("Error checking git version:", err)
		missing = append(missing, "git")
	}
	log.Println("\n ")
	return missing
}
