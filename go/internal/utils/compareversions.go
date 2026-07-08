package utils

import (
	"strconv"
	"strings"
)

// IsVersionAtLeast checks if the current version meets or exceeds the target minimum version.
// Example: IsVersionAtLeast("3.10.18", "3.10.0") -> true
// Example: IsVersionAtLeast("9.0.3", "22.0.0")  -> false
func IsVersionAtLeast(current, minimum string) bool {
	// Clean out prefixes like "Python " or "pip " if they exist
	current = strings.TrimSpace(strings.ReplaceAll(strings.ReplaceAll(current, "Python", ""), "pip", ""))
	minimum = strings.TrimSpace(strings.ReplaceAll(strings.ReplaceAll(minimum, "Python", ""), "pip", ""))

	// Split strings by the decimal dots (e.g., "3.10.18" -> ["3", "10", "18"])
	currParts := strings.Split(current, ".")
	minParts := strings.Split(minimum, ".")

	// Find out how deep we need to compare (usually 2 or 3 positions)
	maxLen := len(currParts)
	if len(minParts) > maxLen {
		maxLen = len(minParts)
	}

	for i := 0; i < maxLen; i++ {
		var currNum, minNum int

		// Convert current segment to integer (fallback to 0 if missing)
		if i < len(currParts) {
			currNum, _ = strconv.Atoi(currParts[i])
		}
		// Convert minimum segment to integer (fallback to 0 if missing)
		if i < len(minParts) {
			minNum, _ = strconv.Atoi(minParts[i])
		}

		// If the current number is bigger, we definitely pass! (e.g., 4.0.0 > 3.10.0)
		if currNum > minNum {
			return true
		}
		// If the current number is smaller, we definitely fail! (e.g., 2.7.0 < 3.10.0)
		if currNum < minNum {
			return false
		}
		// If they are equal, the loop moves to the next decimal place (Minor, then Patch)
	}

	// If the loop finished and everything matched exactly, it's the exact same version
	return true
}
