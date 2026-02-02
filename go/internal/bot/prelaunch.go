package bot

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"strings"

	"github.com/mistromy/Nirupama/internal/bootstrap"
)

func GitUpdate() {
	cmd := exec.Command("git", "pull")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Println("Error updating from git:", err)
		return
	}
}

func InstallDependencies(paths bootstrap.SystemSpecific) {
	requirementsPath := findFilepath("requirements.txt")
	if requirementsPath == "" {
		fmt.Println("No requirements.txt found.")
		return
	}
	fmt.Println("Installing dependencies from: " + requirementsPath + "requirements.txt")
	cmd := exec.Command(paths.Pip, "install", "-r", requirementsPath+"requirements.txt")
	stdout, _ := cmd.StdoutPipe()
	cmd.Stderr = os.Stderr
	err := cmd.Start()
	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "Requirement already satisfied:") {
			continue
		}
	}
	err = cmd.Wait()
	if err != nil {
		fmt.Println("Error installing dependencies:", err)
		return
	}
}
