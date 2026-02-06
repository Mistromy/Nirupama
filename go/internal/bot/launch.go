package bot

import (
	"bufio"
	"log"
	"os"
	"os/exec"

	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/utils/paths"
)

func Start() {
	systemSpecificTools := bootstrap.GetSystemSpecific()
	filepath := paths.GetPath("pybot", "main.py")
	log.Println("Starting bot from: " + filepath + "main.py")
	if filepath == "" {
		return
	}
	cmd := exec.Command(systemSpecificTools.Python, filepath+"main.py")
	stdout, _ := cmd.StdoutPipe()
	cmd.Stderr = os.Stderr
	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		log.Println(line)
	}
	err := cmd.Start()
	if err != nil {
		log.Println("Error starting bot:", err)
		return
	}
}
