package utils

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
)

func RunAndLog(name string, args ...string) {
	fmt.Println(name, strings.Join(args, " "))
	cmd := exec.Command(name, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		// Reconstruct the full command line text so you know exactly what failed
		fullCmd := name + " " + strings.Join(args, " ")

		log.Fatalf("\n[CRITICAL FAILURE] Setup halted.\nCommand: %s\nError: %v\n", fullCmd, err)
	}
}
