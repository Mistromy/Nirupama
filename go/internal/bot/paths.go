package bot

import (
	"fmt"
	"os"
)

var Locations []string = []string{"../../pybot/", "../../../pybot/", "../../", "../../../"}

func findFilepath(filename string) string {
	for i := range Locations {
		fmt.Println("Searching: " + Locations[i] + filename)
		_, err := os.Stat(Locations[i] + filename)
		foundloc := Locations[i]
		if err != nil {
			continue
		}
		return foundloc
	}
	return ""
}
