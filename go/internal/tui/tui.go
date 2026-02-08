package tui

import (
	"log"
	"os/exec"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/mistromy/Nirupama/internal/tui/components/console"
)

type BotProcMsg struct {
	Cmd *exec.Cmd
}

type model struct {
	focus    window
	viewport console.Model
	botCmd   *exec.Cmd
}

type window int

const (
	Console window = iota
	QuickOptions
)

func initialModel() model {
	return model{
		focus:    0,
		viewport: console.Model{},
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {

	case tea.WindowSizeMsg:
		consoleWidth := int(float64(msg.Width) * 0.65)
		consoleHeight := msg.Height
		consoleMsg := tea.WindowSizeMsg{
			Width:  consoleWidth,
			Height: consoleHeight,
		}
		m.viewport, cmd = m.viewport.Update(consoleMsg)
		return m, cmd

	case BotProcMsg:
		m.botCmd = msg.Cmd
		return m, cmd

	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			if m.botCmd != nil && m.botCmd.Process != nil {
				m.viewport, _ = m.viewport.Update("Stopping Nirupama.\n")
				m.botCmd.Process.Kill()
			}
			return m, tea.Quit
		}
	case tea.MouseMsg:
		m.viewport, cmd = m.viewport.Update(msg)
		return m, cmd

	case string:
		m.viewport, cmd = m.viewport.Update(msg)
		return m, cmd
	}
	return m, cmd
}

func (m model) View() string {
	return m.viewport.View()
}

type LogWriter struct {
	Program *tea.Program
}

func (lw *LogWriter) Write(p []byte) (n int, err error) {
	logMessage := string(p)
	lw.Program.Send(logMessage)
	return len(p), nil
}

func StartDashboard(startFunctions func(*tea.Program)) {
	prg := tea.NewProgram(initialModel(), tea.WithMouseCellMotion()) // Define bubble tea program

	log.SetOutput(&LogWriter{Program: prg})

	go startFunctions(prg)

	if _, err := prg.Run(); err != nil {
		log.Println("Error running program:", err)
	}
}
