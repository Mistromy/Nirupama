package main

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type model struct {
	focus    window
	log      []string
	sub      chan string
	viewport viewport.Model
}
type logMsg string
type window int

const (
	Console window = iota
	QuickOptions
)

func initialModel() model {
	return model{
		focus: 0,
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case logMsg:
		m.log = append(m.log, string(msg))
		logs := strings.Join(m.log, "\n")
		m.viewport.SetContent(logs)
		m.viewport.GotoBottom()
		return m, waitForActivity(m.sub)
	}
	return m, nil
}

func (m model) View() string {

	return style.Render(m.viewport.View())

}

var style = lipgloss.NewStyle().
	Foreground(lipgloss.Color("#FAFAFA")).
	Background(lipgloss.Color("#443c5e")).
	Padding(0, 1).
	Border(lipgloss.RoundedBorder()).
	BorderForeground(lipgloss.Color("#7D6EAA"))

func waitForActivity(sub chan string) tea.Cmd {
	return func() tea.Msg {
		return logMsg(<-sub)
	}
}

func dashboard() {
	prg := tea.NewProgram(initialModel())
	if _, err := prg.Run(); err != nil {
		fmt.Println("Error running program:", err)
	}
	// Further CLI implementation would go here
}
