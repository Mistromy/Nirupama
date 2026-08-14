package main

import (
	"os"
	"os/exec"

	"charm.land/log/v2"
)

func main() {
	log.Info("Starting Nirupama...")
	cmd := exec.Command("python3", "pybot/main.py")
	cmd.Stdout, cmd.Stderr, cmd.Stdin = os.Stdout, os.Stderr, os.Stdin
	err := cmd.Run()
	if err != nil {
		log.Fatal(err)
	}
}
