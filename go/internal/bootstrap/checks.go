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
	GitExists      bool
	PipExists      bool
	PythonExists   bool
	CondaExists    bool
	PythonVersion  string
	PipVersion     string
	PackageManager string
}

var Info EnvInfo

func IsFirstStart() bool {
	_, err := os.Stat("pybot/main.py")
	return err != nil
}

func CheckEnvironment() {
	pythonCmd := "python3"
	pipCmd := "pip3"

	_, err := exec.LookPath("git")
	Info.GitExists = (err == nil)
	_, err = exec.LookPath(pipCmd)
	Info.PipExists = (err == nil)
	_, err = exec.LookPath(pythonCmd)
	Info.PythonExists = (err == nil)
	_, err = exec.LookPath("conda")
	Info.CondaExists = (err == nil)

	_, err = exec.LookPath("apt")
	if err == nil {
		Info.PackageManager = "apt"
	} else if _, err = exec.LookPath("yum"); err == nil {
		Info.PackageManager = "yum"
	}

	if Info.PythonExists {
		out, err := exec.Command(pythonCmd, "--version").CombinedOutput()
		if err == nil {
			Info.PythonVersion = strings.TrimSpace(string(out))
		}
	}
	if Info.PipExists {
		out, err := exec.Command(pipCmd, "--version").CombinedOutput()
		if err == nil {
			parts := strings.Split(strings.TrimSpace(string(out)), " ")
			if len(parts) >= 2 {
				Info.PipVersion = parts[0] + " " + parts[1]
			} else {
				Info.PipVersion = strings.TrimSpace(string(out))
			}
		}
	}
}
