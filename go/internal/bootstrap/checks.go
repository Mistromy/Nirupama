package bootstrap

import (
	"os"
	"os/exec"
	"strings"
)

type SystemSpecific struct {
	Pip    string
	Python string
}

type EnvInfo struct {
	GitExists     bool
	PipExists     bool
	PythonExists  bool
	CondaExists   bool
	PythonVersion string
	PipVersion    string
	EnvType       string
}

func IsFirstStart() bool {
	_, err := os.Stat("pybot/main.py")
	return err != nil
}

func CheckEnvironment() EnvInfo {
	pythonCmd := "python3"
	pipCmd := "pip3"
	if os.Getenv("OS") == "Windows_NT" {
		pythonCmd = "python"
		pipCmd = "pip"
	}

	info := EnvInfo{EnvType: "global"}

	_, err := exec.LookPath("git")
	info.GitExists = (err == nil)
	_, err = exec.LookPath(pipCmd)
	info.PipExists = (err == nil)
	_, err = exec.LookPath(pythonCmd)
	info.PythonExists = (err == nil)
	_, err = exec.LookPath("conda")
	info.CondaExists = (err == nil)

	if info.PythonExists {
		out, err := exec.Command(pythonCmd, "--version").CombinedOutput()
		if err == nil {
			info.PythonVersion = strings.TrimSpace(string(out))
		}
	}
	if info.PipExists {
		out, err := exec.Command(pipCmd, "--version").CombinedOutput()
		if err == nil {
			parts := strings.Split(strings.TrimSpace(string(out)), " ")
			if len(parts) >= 2 {
				info.PipVersion = parts[0] + " " + parts[1]
			} else {
				info.PipVersion = strings.TrimSpace(string(out))
			}
		}
	}
	return info
}
