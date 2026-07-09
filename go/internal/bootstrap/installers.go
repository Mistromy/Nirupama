package bootstrap

import (
	"fmt"
	"io"
	"net/http"
	"os"
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

// InstallCondaFlow handles the entire downloading and installation lifecycle safely without root pollution
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
	// FIXED: Wrapped in RunAsUserAndLog to ensure extraction stays in user-space
	utils.RunAsUserAndLog("bash", ScriptPath, "-b", "-p", CondaInstDir)

	utils.CyanLog("[Conda] Creating isolated Python 3.10 environment...")
	// FIXED: Envs are now built safely under the non-root user profile
	condaBin := fmt.Sprintf("%s/bin/conda", CondaInstDir)
	utils.RunAsUserAndLog(condaBin, "create", "-y", "-p", BotEnvDir, "python=3.10")

	utils.CyanLog("[Conda] Setup complete! Upgrading local pip...")
	// FIXED: Upgrades the pip layer entirely inside safe user boundaries
	envPip := fmt.Sprintf("%s/bin/pip", BotEnvDir)
	utils.RunAsUserAndLog(envPip, "install", "--upgrade", "pip")

	return nil
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
	utils.RunAsUserAndLog("git", "init")

	utils.RunAsUserAndLog("git", "remote", "add", "origin", repoURL)
	utils.RunAsUserAndLog("git", "remote", "set-url", "origin", repoURL)

	utils.RunAsUserAndLog("git", "fetch", "--depth=1", "origin", "main")
	utils.RunAsUserAndLog("git", "reset", "--hard", "origin/main")

	utils.CyanLog("Git Repo Installed")
}
