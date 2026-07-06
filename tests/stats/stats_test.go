package stats_test

import (
	"strings"
	"testing"

	"github.com/EdgarOrtegaRamirez/tomlforge/internal/models"
	"github.com/EdgarOrtegaRamirez/tomlforge/internal/parser"
	"github.com/EdgarOrtegaRamirez/tomlforge/internal/stats"
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

func TestAnalyzeBasic(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
port = 8080
debug = true
`)
	s := stats.Analyze(doc)
	if s.TotalKeys != 3 {
		t.Errorf("expected 3 total keys, got %d", s.TotalKeys)
	}
	if s.MaxDepth != 0 {
		t.Errorf("expected depth 0 for flat doc, got %d", s.MaxDepth)
	}
}

func TestAnalyzeNested(t *testing.T) {
	doc := parseDoc(t, `
[server]
host = "localhost"

[server.options]
timeout = 30
`)
	s := stats.Analyze(doc)
	if s.TotalKeys < 3 {
		t.Errorf("expected at least 3 keys, got %d", s.TotalKeys)
	}
	if s.MaxDepth < 1 {
		t.Errorf("expected at least depth 1, got %d", s.MaxDepth)
	}
}

func TestAnalyzeArrays(t *testing.T) {
	doc := parseDoc(t, `
items = [1, 2, 3]
`)
	s := stats.Analyze(doc)
	if s.TotalArrays != 1 {
		t.Errorf("expected 1 array, got %d", s.TotalArrays)
	}
}

func TestAnalyzeEmpty(t *testing.T) {
	doc := &models.Document{Root: make(map[string]*models.Value)}
	s := stats.Analyze(doc)
	if s.TotalKeys != 0 {
		t.Errorf("expected 0 keys, got %d", s.TotalKeys)
	}
}

func TestFormat(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
port = 8080
`)
	s := stats.Analyze(doc)
	output := stats.Format(s)
	if !strings.Contains(output, "Total keys:") {
		t.Errorf("expected formatted output to contain 'Total keys:', got %q", output)
	}
	if !strings.Contains(output, "TOML Document Statistics") {
		t.Errorf("expected header in output")
	}
}

func TestKeyFrequency(t *testing.T) {
	doc := parseDoc(t, `
name = "test"

[a]
name = "a"

[b]
name = "b"
`)
	s := stats.Analyze(doc)
	if s.KeyFrequency["name"] != 3 {
		t.Errorf("expected name frequency=3, got %d", s.KeyFrequency["name"])
	}
}

func TestTypeCounts(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
port = 8080
debug = true
`)
	s := stats.Analyze(doc)
	if s.TypeCounts["string"] != 1 {
		t.Errorf("expected 1 string, got %d", s.TypeCounts["string"])
	}
	if s.TypeCounts["integer"] != 1 {
		t.Errorf("expected 1 integer, got %d", s.TypeCounts["integer"])
	}
	if s.TypeCounts["boolean"] != 1 {
		t.Errorf("expected 1 boolean, got %d", s.TypeCounts["boolean"])
	}
}
