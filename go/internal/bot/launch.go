package bot

import (
	"log"
	"os/exec"

	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/utils/paths"
)

func Start() *exec.Cmd {
	systemSpecificTools := bootstrap.GetSystemSpecific()
	filepath := paths.GetPath("pybot", "main.py")
	log.Println("Starting bot from: " + filepath)
	if filepath == "" {
		return nil
	}
	cmd := exec.Command(systemSpecificTools.Python, "-u", filepath)
	cmd.Stdout = log.Writer()
	cmd.Stderr = log.Writer()

	err := cmd.Start()
	if err != nil {
		log.Println("Error starting bot:", err)
		return nil
	}

	return cmd
}
