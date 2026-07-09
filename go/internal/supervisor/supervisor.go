package supervisor

import "github.com/mistromy/Nirupama/internal/utils"

func LaunchBot() {
	utils.RunAndLog(utils.Python, "pybot/main.py")
}
