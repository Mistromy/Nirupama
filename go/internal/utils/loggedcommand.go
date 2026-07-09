package utils

import (
	"log"
	"os"
	"os/exec"
	"strings"
)

func RunAndLog(name string, args ...string) {
	CyanLog(name, strings.Join(args, " "))
	cmd := exec.Command(name, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		// Reconstruct the full command line text so you know exactly what failed
		fullCmd := name + " " + strings.Join(args, " ")

		log.Fatalf("\n[CRITICAL FAILURE] Setup halted.\nCommand: %s\nError: %v\n", fullCmd, err)
	}
}

func RunAsUserAndLog(name string, args ...string) {
	sudoUser := os.Getenv("SUDO_USER")

	// If the script was run with sudo, prepend "sudo -u username" to drop privileges
	if sudoUser != "" {
		realArgs := append([]string{"-u", sudoUser, name}, args...)
		name = "sudo"
		args = realArgs
	}

	CyanLog(name, strings.Join(args, " "))
	cmd := exec.Command(name, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		fullCmd := name + " " + strings.Join(args, " ")
		log.Fatalf("\n[CRITICAL FAILURE] Setup halted.\nCommand: %s\nError: %v\n", fullCmd, err)
	}
}
