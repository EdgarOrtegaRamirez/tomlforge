package format_test

import (
	"strings"
	"testing"

	"github.com/EdgarOrtegaRamirez/tomlforge/internal/format"
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

func TestFormatDefault(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
port = 8080
`)
	output := format.Format(doc, nil)
	if len(output) == 0 {
		t.Error("expected non-empty output")
	}
	if !strings.Contains(output, "name = \"test\"") {
		t.Errorf("expected formatted output to contain 'name = \"test\"', got %q", output)
	}
}

func TestFormatSorted(t *testing.T) {
	doc := parseDoc(t, `
z = 1
a = 2
m = 3
`)
	output := format.SortKeys(doc)
	lines := strings.Split(strings.TrimSpace(output), "\n")
	if len(lines) < 3 {
		t.Errorf("expected at least 3 lines, got %d", len(lines))
	}
	// Check keys are sorted
	if !strings.Contains(lines[0], "a = 2") {
		t.Errorf("expected first line to be 'a = 2', got %q", lines[0])
	}
}

func TestMinify(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
port = 8080
`)
	output := format.Minify(doc)
	// Minified should have no extra indentation
	if strings.Contains(output, "  ") {
		// It might still have spaces in string values, so just check it's shorter
		pretty := format.Format(doc, nil)
		if len(output) >= len(pretty) {
			t.Errorf("expected minified to be shorter than pretty")
		}
	}
}

func TestFormatCustomIndent(t *testing.T) {
	doc := parseDoc(t, `
[server]
host = "localhost"
`)
	opts := &format.FormatOptions{
		Indent: "\t",
		SortKeys: true,
	}
	output := format.Format(doc, opts)
	if !strings.Contains(output, "\t") {
		t.Errorf("expected tab indentation in output")
	}
}

func TestFormatEmptyDoc(t *testing.T) {
	doc := &models.Document{Root: make(map[string]*models.Value)}
	output := format.Format(doc, nil)
	if len(output) != 0 {
		t.Errorf("expected empty output for empty doc, got %q", output)
	}
}

func TestDefaultOptions(t *testing.T) {
	opts := format.DefaultOptions()
	if opts.Indent != "  " {
		t.Errorf("expected default indent '  ', got %q", opts.Indent)
	}
	if !opts.SortKeys {
		t.Error("expected SortKeys=true by default")
	}
	if !opts.Pretty {
		t.Error("expected Pretty=true by default")
	}
}
