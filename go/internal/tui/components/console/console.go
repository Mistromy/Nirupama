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
		w := msg.Width - style.GetHorizontalFrameSize()
		h := msg.Height - style.GetVerticalFrameSize()
		wrapper := lipgloss.NewStyle().Width(w)
		wrappedContent := wrapper.Render(m.Content)
		if !m.Ready {
			m.Viewport = viewport.New(w, h)
			m.Viewport.SetContent(wrappedContent)
			m.Ready = true
		} else {
			m.Viewport.Width = w
			m.Viewport.Height = h
			m.Viewport.SetContent(wrappedContent)
			m.Viewport.GotoBottom()
		}
	case string:
		m.Content += msg
		wrapper := lipgloss.NewStyle().Width(m.Viewport.Width)
		wrappedContent := wrapper.Render(m.Content)
		m.Viewport.SetContent(wrappedContent)
		m.Viewport.GotoBottom()
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
