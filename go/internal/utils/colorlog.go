package utils

import "fmt"

const (
	ColorCyan  = "\033[96m"
	ColorReset = "\033[0m"
)

// CyanLog prints text wrapped in a light cyan color shell
func CyanLog(format string, a ...interface{}) {
	message := fmt.Sprintf(format, a...)
	fmt.Printf("%s%s%s\n", ColorCyan, message, ColorReset)
}
