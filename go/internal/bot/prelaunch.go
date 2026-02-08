package bot

import (
	"bufio"
	"log"
	"os"
	"os/exec"
	"strings"

	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/utils/paths"
)

func GitUpdate() {
	cmd := exec.Command("git", "pull")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		log.Println("Error updating from git:", err)
		return
	}
}

func InstallDependencies(cmdpaths bootstrap.SystemSpecific) {
	requirementsPath := paths.GetPath("requirements.txt")
	if requirementsPath == "" {
		log.Println("No requirements.txt found.\n ")
		return
	}
	log.Println("Installing dependencies from: " + requirementsPath)
	cmd := exec.Command(cmdpaths.Pip, "install", "-r", requirementsPath)
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
		log.Println("Error installing dependencies:", err)
		return
	}
}
