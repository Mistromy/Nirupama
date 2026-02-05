package bootstrap

import (
	"fmt"
	"os"
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
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Println("Error checking Python version:", err)
		missing = append(missing, "python")
	}
	cmd = exec.Command(systemSpecificTools.Pip, "--version")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err = cmd.Run()
	if err != nil {
		fmt.Println("Error checking pip version:", err)
		missing = append(missing, "pip")
	}
	cmd = exec.Command("git", "--version")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err = cmd.Run()
	if err != nil {
		fmt.Println("Error checking git version:", err)
		missing = append(missing, "git")
	}
	fmt.Println("\n ")
	return missing
}
