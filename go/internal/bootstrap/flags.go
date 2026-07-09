package bootstrap

import (
	"flag"

	"github.com/mistromy/Nirupama/internal/utils"
)

func ParseFlags() {
	// Bind the -y flag directly to the utils variable destination
	flag.BoolVar(&utils.AutoConfirm, "y", false, "Auto-confirm all installation prompts")
	flag.Parse()
}
