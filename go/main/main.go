package main

import (
	"fmt"
	"os"
	"os/exec"
)

var Locations []string = defaults()

func defaults() []string {
	locations := []string{"pybot/", "../../pybot/", "", "../../"}
	return locations
}

func main() {
	start()
	// tick()
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

func installDependencies() {
	requirementsPath := findFilepath("requirements.txt")
	if requirementsPath == "" {
		fmt.Println("No requirements.txt found.")
		return
	}
	fmt.Println("Installing dependencies from: " + requirementsPath + "requirements.txt")
	cmd := exec.Command("pip3", "install", "-r", requirementsPath+"requirements.txt")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Println("Error installing dependencies:", err)
		return
	}
}

func start() {
	installDependencies()
	filepath := findFilepath("main.py")
	fmt.Println("Starting bot from: " + filepath + "main.py")
	if filepath == "" {
		return
	}
	cmd := exec.Command("python3", filepath+"main.py")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Println("Error starting bot:", err)
		return
	}
}

// func tick() {
// 	for {
// 	}
// }
