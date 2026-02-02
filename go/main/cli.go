package main

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
)

var style = lipgloss.NewStyle().
	Foreground(lipgloss.Color("#FAFAFA")).
	Background(lipgloss.Color("#443c5e")).
	Padding(0, 1).
	Border(lipgloss.NormalBorder()).
	BorderForeground(lipgloss.Color("#7D6EAA"))

func testRender() {
	fmt.Println(style.Render("Nirupama Bot CLI"))
	// Further CLI implementation would go here
}
