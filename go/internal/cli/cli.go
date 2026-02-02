package cli

import (
	"fmt"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type model struct {
	focus window
	log   []string
}

type window int

const (
	Console window = iota
	QuickOptions
)

func initialModel() model {
	return model{
		focus: 0,
		log:   []string{},
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	return m, nil
}

func (m model) View() string {
	return ""
}

var style = lipgloss.NewStyle().
	Foreground(lipgloss.Color("#FAFAFA")).
	Background(lipgloss.Color("#443c5e")).
	Padding(0, 1).
	Border(lipgloss.RoundedBorder()).
	BorderForeground(lipgloss.Color("#7D6EAA"))

func StartDashboard() {
	prg := tea.NewProgram(initialModel())
	if _, err := prg.Run(); err != nil {
		fmt.Println("Error running program:", err)
	}
}
