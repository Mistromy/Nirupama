package paths

import (
	"fmt"
	"os"
	"path/filepath"
)

var Locations []string = []string{"../../pybot/", "../../../pybot/", "../../", "../../../"}
var RootLocation string = ""

// #TODO: Finish Refactoring this thing
func FindRoot() (string, error) {
	exepath, _ := os.Executable()
	temppath := filepath.Dir(exepath)
	for {
		testpath := filepath.Join(temppath, "pybot")
		osstat, _ := os.Stat(testpath)
		if osstat != nil {
			RootLocation = temppath
			break
		}
		temppath = filepath.Dir(temppath)
	}
	fmt.Println(RootLocation)
	return RootLocation, nil
}

func GetPath(file ...string) string {
	filepath := filepath.Join(RootLocation, filepath.Join(file...))
	return filepath
}
