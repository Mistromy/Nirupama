package bot

import (
	"log"
	"os/exec"

	"github.com/mistromy/Nirupama/internal/utils"
)

func Start() *exec.Cmd {
	utils.CyanLog("Starting bot...")
	cmd := exec.Command(utils.Python, "pybot/main.py")
	cmd.Stdout = log.Writer()
	cmd.Stderr = log.Writer()

	err := cmd.Start()
	if err != nil {
		log.Println("Error starting bot:", err)
		return nil
	}

	return cmd
}
