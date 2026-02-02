package main

import (
	"fmt"
	"os"
	"os/exec"
)

func CheckRequirements() []string {
	missing := []string{}
	cmd := exec.Command(SystemSpecificTools.python, "--version")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Println("Error checking Python version:", err)
		missing = append(missing, "python")
	}
	cmd = exec.Command(SystemSpecificTools.pip, "--version")
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
	return missing
}
