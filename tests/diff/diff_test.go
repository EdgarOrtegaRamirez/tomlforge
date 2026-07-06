package diff_test

import (
	"strings"
	"testing"

	"github.com/EdgarOrtegaRamirez/tomlforge/internal/diff"
	"github.com/EdgarOrtegaRamirez/tomlforge/internal/models"
	"github.com/EdgarOrtegaRamirez/tomlforge/internal/parser"
)

func parseDoc(t *testing.T, input string) *models.Document {
	t.Helper()
	p := parser.New()
	doc, err := p.Parse(input)
	if err != nil {
		t.Fatalf("failed to parse: %v", err)
	}
	return doc
}

func TestDiffIdentical(t *testing.T) {
	input := `name = "test"`
	doc1 := parseDoc(t, input)
	doc2 := parseDoc(t, input)

	result := diff.Diff(doc1, doc2)
	if result.Summary.Added != 0 || result.Summary.Removed != 0 || result.Summary.Modified != 0 {
		t.Errorf("expected no changes, got %v", result.Summary)
	}
}

func TestDiffAdded(t *testing.T) {
	doc1 := parseDoc(t, `name = "test"`)
	doc2 := parseDoc(t, `
name = "test"
port = 8080
`)

	result := diff.Diff(doc1, doc2)
	if result.Summary.Added != 1 {
		t.Errorf("expected 1 added, got %d", result.Summary.Added)
	}
	found := false
	for _, e := range result.Entries {
		if e.Type == diff.ChangeAdded && e.Path == "port" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected added entry for 'port'")
	}
}

func TestDiffRemoved(t *testing.T) {
	doc1 := parseDoc(t, `
name = "test"
port = 8080
`)
	doc2 := parseDoc(t, `name = "test"`)

	result := diff.Diff(doc1, doc2)
	if result.Summary.Removed != 1 {
		t.Errorf("expected 1 removed, got %d", result.Summary.Removed)
	}
}

func TestDiffModified(t *testing.T) {
	doc1 := parseDoc(t, `name = "old"`)
	doc2 := parseDoc(t, `name = "new"`)

	result := diff.Diff(doc1, doc2)
	if result.Summary.Modified != 1 {
		t.Errorf("expected 1 modified, got %d", result.Summary.Modified)
	}
}

func TestDiffNested(t *testing.T) {
	doc1 := parseDoc(t, `
[server]
host = "localhost"
port = 3000
`)
	doc2 := parseDoc(t, `
[server]
host = "localhost"
port = 8080
`)

	result := diff.Diff(doc1, doc2)
	if result.Summary.Modified != 1 {
		t.Errorf("expected 1 modified, got %d", result.Summary.Modified)
	}
	found := false
	for _, e := range result.Entries {
		if e.Type == diff.ChangeModified && e.Path == "server.port" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected modified entry for 'server.port'")
	}
}

func TestFormatText(t *testing.T) {
	doc1 := parseDoc(t, `name = "old"`)
	doc2 := parseDoc(t, `name = "new"`)

	result := diff.Diff(doc1, doc2)
	text := diff.FormatText(result)

	if !strings.Contains(text, "~ name:") {
		t.Errorf("expected text format to contain modification, got %q", text)
	}
}

func TestFormatCompact(t *testing.T) {
	doc1 := parseDoc(t, `name = "old"`)
	doc2 := parseDoc(t, `name = "new"`)

	result := diff.Diff(doc1, doc2)
	text := diff.FormatCompact(result)

	if !strings.Contains(text, "~name") {
		t.Errorf("expected compact format to contain ~name, got %q", text)
	}
}

func TestChangeTypeString(t *testing.T) {
	tests := []struct {
		ct   diff.ChangeType
		want string
	}{
		{diff.ChangeAdded, "added"},
		{diff.ChangeRemoved, "removed"},
		{diff.ChangeModified, "modified"},
		{diff.ChangeUnchanged, "unchanged"},
	}
	for _, tt := range tests {
		if got := tt.ct.String(); got != tt.want {
			t.Errorf("ChangeType.String() = %q, want %q", got, tt.want)
		}
	}
}
