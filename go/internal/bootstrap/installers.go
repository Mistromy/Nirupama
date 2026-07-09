package bootstrap

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"runtime"

	"github.com/mistromy/Nirupama/internal/utils"
)

func installGit() {
	utils.RunAndLog("sudo", Info.PackageManager, "install", "-y", "git")
}

const (
	CondaInstDir = "./engine/conda"
	BotEnvDir    = "./engine/bot_env"
	ScriptPath   = "./miniconda.sh"
)

// InstallCondaFlow handles the entire downloading and installation lifecycle
func installCondaFlow() error {
	// 1. Detect Architecture and Pick URL
	url := "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh" // Default Intel/AMD
	if runtime.GOARCH == "arm64" {
		url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh" // Oracle ARM Fallback
	}

	utils.CyanLog("[Conda] Detecting architecture: %s. Downloading installer...", runtime.GOARCH)
	if err := downloadFile(ScriptPath, url); err != nil {
		return fmt.Errorf("failed to download installer: %w", err)
	}
	defer os.Remove(ScriptPath) // Cleans up the .sh installer file when done

	utils.CyanLog("[Conda] Running silent batch installer...")
	// Run: bash miniconda.sh -b -p ./engine/conda
	cmdInstall := exec.Command("bash", ScriptPath, "-b", "-p", CondaInstDir)
	cmdInstall.Stdout = os.Stdout
	cmdInstall.Stderr = os.Stderr
	if err := cmdInstall.Run(); err != nil {
		return fmt.Errorf("silent installation failed: %w", err)
	}

	utils.CyanLog("[Conda] Creating isolated Python 3.10 environment...")
	// Run: ./engine/conda/bin/conda create -y -p ./engine/bot_env python=3.10
	condaBin := fmt.Sprintf("%s/bin/conda", CondaInstDir)
	cmdEnv := exec.Command(condaBin, "create", "-y", "-p", BotEnvDir, "python=3.10")
	cmdEnv.Env = append(os.Environ(), "CONDA_PLUGINS_AUTO_ACCEPT_TOS=yes")
	cmdEnv.Stdout = os.Stdout
	cmdEnv.Stderr = os.Stderr
	if err := cmdEnv.Run(); err != nil {
		return fmt.Errorf("environment creation failed: %w", err)
	}

	utils.CyanLog("[Conda] Setup complete! Upgrading local pip...")
	// Upgrade the pip inside your brand new environment immediately
	envPip := fmt.Sprintf("%s/bin/pip", BotEnvDir)
	cmdPip := exec.Command(envPip, "install", "--upgrade", "pip")
	return cmdPip.Run()
}

// Reusable native helper to stream a download file to disk without heavy memory overhead
func downloadFile(filepath string, url string) error {
	out, err := os.Create(filepath)
	if err != nil {
		return err
	}
	defer out.Close()

	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("bad status: %s", resp.Status)
	}

	_, err = io.Copy(out, resp.Body)
	return err
}

func installRepo() {
	repoURL := "https://github.com/mistromy/Nirupama.git"

	utils.CyanLog("Initializing git and fetching latest deployment layer...")
	RunAndLog("git", "init")

	exec.Command("git", "remote", "add", "origin", repoURL).Run()
	exec.Command("git", "remote", "set-url", "origin", repoURL).Run()

	RunAndLog("git", "fetch", "--depth=1", "origin", "main")

	RunAndLog("git", "reset", "--hard", "origin/main")

	utils.CyanLog("Git Repo Installed")
}
