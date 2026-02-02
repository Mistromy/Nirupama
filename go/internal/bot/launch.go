package bot

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"

	"github.com/mistromy/Nirupama/internal/bootstrap"
)

func Start(log chan string) {
	systemSpecificTools := bootstrap.GetSystemSpecific()
	filepath := findFilepath("main.py")
	fmt.Println("Starting bot from: " + filepath + "main.py")
	if filepath == "" {
		return
	}
	cmd := exec.Command(systemSpecificTools.Python, filepath+"main.py")
	stdout, _ := cmd.StdoutPipe()
	cmd.Stderr = os.Stderr
	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		log <- line
	}
	err := cmd.Start()
	if err != nil {
		fmt.Println("Error starting bot:", err)
		return
	}
}
