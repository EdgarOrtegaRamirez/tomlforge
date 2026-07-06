package parser_test

import (
	"testing"

	"github.com/EdgarOrtegaRamirez/tomlforge/internal/parser"
)

func TestParseSimple(t *testing.T) {
	input := `
name = "test"
port = 8080
debug = true
`
	p := parser.New()
	doc, err := p.Parse(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if v := doc.GetPath("name"); v == nil || v.Str != "test" {
		t.Errorf("expected name='test', got %v", v)
	}
	if v := doc.GetPath("port"); v == nil || v.Int != 8080 {
		t.Errorf("expected port=8080, got %v", v)
	}
	if v := doc.GetPath("debug"); v == nil || !v.Bool {
		t.Errorf("expected debug=true, got %v", v)
	}
}

func TestParseNestedTable(t *testing.T) {
	input := `
[server]
host = "localhost"
port = 3000

[database]
driver = "postgres"
`
	p := parser.New()
	doc, err := p.Parse(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if v := doc.GetPath("server.host"); v == nil || v.Str != "localhost" {
		t.Errorf("expected server.host='localhost', got %v", v)
	}
	if v := doc.GetPath("server.port"); v == nil || v.Int != 3000 {
		t.Errorf("expected server.port=3000, got %v", v)
	}
	if v := doc.GetPath("database.driver"); v == nil || v.Str != "postgres" {
		t.Errorf("expected database.driver='postgres', got %v", v)
	}
}

func TestParseArray(t *testing.T) {
	input := `
colors = ["red", "green", "blue"]
numbers = [1, 2, 3]
`
	p := parser.New()
	doc, err := p.Parse(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	v := doc.GetPath("colors")
	if v == nil {
		t.Fatal("expected colors array")
	}
	arr, ok := v.AsArray()
	if !ok || len(arr) != 3 {
		t.Errorf("expected 3 colors, got %d", len(arr))
	}
}

func TestParseArrayOfTables(t *testing.T) {
	input := `
[[servers]]
name = "server1"
port = 8080

[[servers]]
name = "server2"
port = 8081
`
	p := parser.New()
	doc, err := p.Parse(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	v := doc.GetPath("servers")
	if v == nil {
		t.Fatal("expected servers array")
	}
	arr, ok := v.AsArray()
	if !ok || len(arr) != 2 {
		t.Errorf("expected 2 servers, got %d", len(arr))
	}
}

func TestParseInvalid(t *testing.T) {
	input := `this is not valid toml = `
	p := parser.New()
	_, err := p.Parse(input)
	if err == nil {
		t.Error("expected error for invalid TOML")
	}
}

func TestValidate(t *testing.T) {
	input := `
name = "test"
port = 8080
`
	p := parser.New()
	err := p.Validate(input)
	if err != nil {
		t.Errorf("expected valid TOML, got error: %v", err)
	}
}

func TestParseFloat(t *testing.T) {
	input := `pi = 3.14159`
	p := parser.New()
	doc, err := p.Parse(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	v := doc.GetPath("pi")
	if v == nil {
		t.Fatal("expected pi value")
	}
	f, ok := v.AsFloat()
	if !ok || f != 3.14159 {
		t.Errorf("expected pi=3.14159, got %f", f)
	}
}

func TestParseEmpty(t *testing.T) {
	input := ``
	p := parser.New()
	doc, err := p.Parse(input)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(doc.Keys()) != 0 {
		t.Errorf("expected 0 keys, got %d", len(doc.Keys()))
	}
}
