package bot

import (
	"testing"

	"github.com/mistromy/Nirupama/internal/utils/paths"
)

func TestFindRoot(t *testing.T) {
	result, err := paths.FindRoot() // <--- We just CALL it. We don't define it here.

	// C. ASSERT (Check if it worked)
	if err != nil {
		t.Errorf("FindRoot failed unexpectedly: %v", err)
	}

	// Optional: Check if the result looks right
	if result == "" {
		t.Error("Expected a path, but got an empty string")
	}

	// Just for you to see it
	t.Logf("Success! Found root at: %s", result)
}
