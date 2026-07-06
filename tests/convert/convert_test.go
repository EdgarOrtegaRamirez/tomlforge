package convert_test

import (
	"encoding/json"
	"strings"
	"testing"

	"github.com/EdgarOrtegaRamirez/tomlforge/internal/convert"
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

func TestToJSON(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
port = 8080
debug = true
`)
	jsonStr, err := convert.ToJSON(doc)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	var data map[string]interface{}
	if err := json.Unmarshal([]byte(jsonStr), &data); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	if data["name"] != "test" {
		t.Errorf("expected name='test', got %v", data["name"])
	}
	if data["port"] != float64(8080) {
		t.Errorf("expected port=8080, got %v", data["port"])
	}
}

func TestToJSONCompact(t *testing.T) {
	doc := parseDoc(t, `name = "test"`)
	jsonStr, err := convert.ToJSONCompact(doc)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if strings.Contains(jsonStr, "\n") {
		t.Errorf("expected compact JSON without newlines")
	}
}

func TestToFlatJSON(t *testing.T) {
	doc := parseDoc(t, `
[server]
host = "localhost"
port = 3000
`)
	jsonStr, err := convert.ToFlatJSON(doc)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	var data map[string]interface{}
	if err := json.Unmarshal([]byte(jsonStr), &data); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	if data["server.host"] != "localhost" {
		t.Errorf("expected server.host='localhost', got %v", data["server.host"])
	}
}

func TestToYAML(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
port = 8080
`)
	yaml := convert.ToYAML(doc)
	if !strings.Contains(yaml, "name: \"test\"") {
		t.Errorf("expected YAML to contain 'name: \"test\"', got %q", yaml)
	}
	if !strings.Contains(yaml, "port: 8080") {
		t.Errorf("expected YAML to contain 'port: 8080', got %q", yaml)
	}
}

func TestToMarkdown(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
port = 8080
`)
	md := convert.ToMarkdown(doc)
	if !strings.Contains(md, "| Key | Type | Value |") {
		t.Errorf("expected markdown table header")
	}
	if !strings.Contains(md, "name") {
		t.Errorf("expected markdown to contain 'name'")
	}
}

func TestToCSV(t *testing.T) {
	doc := parseDoc(t, `
[[items]]
name = "a"
value = 1

[[items]]
name = "b"
value = 2
`)
	csv, err := convert.ToCSV(doc)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !strings.Contains(csv, "name,value") {
		t.Errorf("expected CSV header, got %q", csv)
	}
	if !strings.Contains(csv, "a,1") {
		t.Errorf("expected CSV row 'a,1', got %q", csv)
	}
}
