package bot

import (
	"log"
	"os/exec"
)

func Start() *exec.Cmd {
	cmd := exec.Command("python3", "pybot/main.py")
	cmd.Stdout = log.Writer()
	cmd.Stderr = log.Writer()

	err := cmd.Start()
	if err != nil {
		log.Println("Error starting bot:", err)
		return nil
	}

	return cmd
}
