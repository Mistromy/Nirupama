package main

import (
	"fmt"
	"os"
	"os/exec"
)

var Locations []string = defaults()

func defaults() []string {
	botLocations := []string{"pybot/main.py", "../../pybot/main.py"}
	return botLocations
}

func main() {
	start()
	// tick()
}

func findFilepath() string {
	for i := range Locations {
		fmt.Println("Searching: " + Locations[i])
		_, err := os.Stat(Locations[i])
		foundloc := Locations[i]
		if err != nil {
			continue
		}
		fmt.Println("Starting " + Locations[i])
		return foundloc
	}
	return ""
}

func start() {
	filepath := findFilepath()
	cmd := exec.Command("python3", filepath)
	cmd.Stdout = os.Stdout
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
