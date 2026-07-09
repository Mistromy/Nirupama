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

	if sudoUser != "" {
		realArgs := append([]string{"-u", sudoUser, "env", "CONDA_PLUGINS_AUTO_ACCEPT_TOS=yes", name}, args...)
		name = "sudo"
		args = realArgs
	}

	CyanLog(name, strings.Join(args, " "))
	cmd := exec.Command(name, args...)

	// Fallback path: keeps it working perfectly if running without sudo as well
	cmd.Env = append(os.Environ(), "CONDA_PLUGINS_AUTO_ACCEPT_TOS=yes")

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		fullCmd := name + " " + strings.Join(args, " ")
		log.Fatalf("\n[CRITICAL FAILURE] Command failed.\nCommand: %s\nError: %v\n", fullCmd, err)
	}
}
