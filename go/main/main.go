package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strings"
)

var Locations []string = defaults()
var SystemSpecificTools systemSpecific

func defaults() []string {
	locations := []string{"pybot/", "../../pybot/", "", "../../"}
	return locations
}

type systemSpecific struct {
	pip    string
	python string
}

func getSystemSpecific() {
	if runtime.GOOS == "windows" {
		SystemSpecificTools.pip = "pip"
		SystemSpecificTools.python = "python"
	} else {
		SystemSpecificTools.pip = "pip3"
		SystemSpecificTools.python = "python3"
	}
}

func findFilepath(filename string) string {
	for i := range Locations {
		fmt.Println("Searching: " + Locations[i] + filename)
		_, err := os.Stat(Locations[i] + filename)
		foundloc := Locations[i]
		if err != nil {
			continue
		}
		return foundloc
	}
	return ""
}

func gitUpdate() {
	cmd := exec.Command("git", "pull")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Println("Error updating from git:", err)
		return
	}
}

func installDependencies() {
	requirementsPath := findFilepath("requirements.txt")
	if requirementsPath == "" {
		fmt.Println("No requirements.txt found.")
		return
	}
	fmt.Println("Installing dependencies from: " + requirementsPath + "requirements.txt")
	cmd := exec.Command(SystemSpecificTools.pip, "install", "-r", requirementsPath+"requirements.txt")
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

func main() {
	getSystemSpecific()

	if m := CheckExternalDependencies(); len(m) > 0 {
		fmt.Println("The Following Requirments could not be found:", m)
		return
	}
	gitUpdate()
	installDependencies()
	start()
	// tick()
}

func start() {
	testRender()
	filepath := findFilepath("main.py")
	fmt.Println("Starting bot from: " + filepath + "main.py")
	if filepath == "" {
		return
	}
	cmd := exec.Command(SystemSpecificTools.python, filepath+"main.py")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Println("Error starting bot:", err)
		return
	}
}
