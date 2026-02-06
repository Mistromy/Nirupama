package tui

import (
	"log"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/mistromy/Nirupama/internal/tui/components/viewport"
)

type model struct {
	focus    window
	viewport viewport.Model
}

type window int

const (
	Console window = iota
	QuickOptions
)

func initialModel() model {
	return model{
		focus:    0,
		viewport: viewport.Model{},
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.viewport, cmd = m.viewport.Update(msg)

	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		}
	}
	return m, cmd
}

func (m model) View() string {
	return m.viewport.View()
}

func StartDashboard() {
	prg := tea.NewProgram(initialModel())
	if _, err := prg.Run(); err != nil {
		log.Println("Error running program:", err)
	}
}
