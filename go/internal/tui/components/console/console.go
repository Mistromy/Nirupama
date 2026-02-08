package console

import (
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type Model struct {
	Content  string
	Ready    bool
	Viewport viewport.Model
}

func New() Model {
	return Model{
		Content: "Starting Nirupama.\n",
		Ready:   false,
	}
}

func (m Model) Init() tea.Cmd {
	return nil
}

func (m Model) Update(msg tea.Msg) (Model, tea.Cmd) {
	var (
		cmd  tea.Cmd
		cmds []tea.Cmd
	)
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		w := msg.Width - 2
		h := msg.Height - 2
		if !m.Ready {
			m.Viewport = viewport.New(w, h)
			m.Viewport.SetContent(m.Content)
			m.Ready = true
		} else {
			m.Viewport.Width = w
			m.Viewport.Height = h
			m.Viewport.GotoBottom()
		}
	case string:
		m.Content += msg
		m.Viewport.SetContent(m.Content)
		m.Viewport.GotoBottom()
	case tea.MouseMsg:

	}
	m.Viewport, cmd = m.Viewport.Update(msg)
	cmds = append(cmds, cmd)
	return m, tea.Batch(cmds...)
}

func (m Model) View() string {
	if !m.Ready {
		return "Loading..."
	}
	return style.Render(m.Viewport.View())
}

var (
	style = lipgloss.NewStyle().
		BorderStyle(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("62")).
		PaddingLeft(1).
		PaddingRight(1)
	titleStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("230")).
			Background(lipgloss.Color("62")).
			Padding(0, 1)
)
