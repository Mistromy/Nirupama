package utils

import (
	"bufio"
	"os"
	"strings"
)

var AutoConfirm bool

// AskYesNo prints a question and waits for the user to input y/n.
// Returns true for yes, false for no.
func AskYesNo(question string) bool {
	// 1. If the auto-confirm flag is active, instantly skip the prompt and return true
	if AutoConfirm {
		CyanLog("[Auto-Confirm] Automatically accepting: %s", question)
		return true
	}

	reader := bufio.NewReader(os.Stdin)

	for {
		CyanLog("%s (y/n): ", question)

		// Read text until the user hits Enter
		input, err := reader.ReadString('\n')
		if err != nil {
			return false
		}

		// Clean up the text (strip spaces and windows newline tags \r\n)
		input = strings.TrimSpace(strings.ToLower(input))

		if input == "y" || input == "yes" {
			return true
		}
		if input == "n" || input == "no" {
			return false
		}

		// If they typed junk, the loop repeats until they give a valid answer
		CyanLog("Invalid input. Please type 'y' or 'n'.")
	}
}
