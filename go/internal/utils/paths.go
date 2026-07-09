package utils

import "os"

// Global variables you can access from anywhere
var Python string
var Pip string

func CheckPaths() {
	// 1. Set default global fallbacks first
	Python = "python3"
	Pip = "pip3"

	// 2. Check if the engine folder environment exists
	if _, err := os.Stat("./engine/bot_env/bin/python"); err == nil {
		Python = "./engine/bot_env/bin/python"
		Pip = "./engine/bot_env/bin/pip"
		return
	}

	// 3. Check if the native .venv folder exists
	if _, err := os.Stat("./.venv/bin/python"); err == nil {
		Python = "./.venv/bin/python"
		Pip = "./.venv/bin/pip"
		return
	}
}
