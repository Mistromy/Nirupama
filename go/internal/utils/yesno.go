package utils

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// AskYesNo prints a question and waits for the user to input y/n.
// Returns true for yes, false for no.
func AskYesNo(question string) bool {
	reader := bufio.NewReader(os.Stdin)

	for {
		fmt.Printf("%s (y/n): ", question)

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
		fmt.Println("Invalid input. Please type 'y' or 'n'.")
	}
}
