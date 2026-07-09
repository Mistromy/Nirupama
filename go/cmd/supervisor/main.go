package main

import (
	"github.com/mistromy/Nirupama/internal/bootstrap"
	"github.com/mistromy/Nirupama/internal/supervisor"
	"github.com/mistromy/Nirupama/internal/utils"
)

func main() {
	bootstrap.ParseFlags()
	bootstrap.Bootstrap()

	utils.CheckPaths()
	supervisor.LaunchBot()
}
