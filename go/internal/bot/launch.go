package bot

import (
	"log"
	"os"
	"os/exec"

	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/utils/paths"
)

func Start() {
	systemSpecificTools := bootstrap.GetSystemSpecific()
	filepath := paths.GetPath("pybot", "main.py")
	log.Println("Starting bot from: " + filepath)
	if filepath == "" {
		return
	}
	cmd := exec.Command(systemSpecificTools.Python, filepath)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err := cmd.Run()
	if err != nil {
		log.Println("Error starting bot:", err)
		return
	}
}
