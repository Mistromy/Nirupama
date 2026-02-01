package main

import (
	"fmt"
	"os/exec"
)

var Location string = defaults()

func defaults() string {
	botLocation := "../../pybot/main.py"
	return botLocation
}

func main() {
	start()
	// tick()
}

func start() {
	fmt.Println(Location)
	cmd := exec.Command("python3", Location)
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
