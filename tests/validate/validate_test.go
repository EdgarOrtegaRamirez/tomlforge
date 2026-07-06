package validate_test

import (
	"testing"

	"github.com/EdgarOrtegaRamirez/tomlforge/internal/models"
	"github.com/EdgarOrtegaRamirez/tomlforge/internal/parser"
	"github.com/EdgarOrtegaRamirez/tomlforge/internal/validate"
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

func TestValidateNilSchema(t *testing.T) {
	doc := parseDoc(t, `name = "test"`)
	result := validate.Validate(doc, nil)
	if !result.Valid {
		t.Error("expected valid with nil schema")
	}
}

func TestValidateRequired(t *testing.T) {
	doc := parseDoc(t, `name = "test"`)
	schema := &validate.Schema{
		Required: []string{"name", "port"},
	}

	result := validate.Validate(doc, schema)
	if result.Valid {
		t.Error("expected invalid due to missing 'port'")
	}
	if len(result.Issues) != 1 {
		t.Errorf("expected 1 issue, got %d", len(result.Issues))
	}
}

func TestValidateRequiredPresent(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
port = 8080
`)
	schema := &validate.Schema{
		Required: []string{"name", "port"},
	}

	result := validate.Validate(doc, schema)
	if !result.Valid {
		t.Errorf("expected valid, got issues: %v", result.Issues)
	}
}

func TestValidateTypes(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
port = 8080
debug = true
`)
	schema := &validate.Schema{
		Types: map[string]string{
			"name":  "string",
			"port":  "integer",
			"debug": "boolean",
		},
	}

	result := validate.Validate(doc, schema)
	if !result.Valid {
		t.Errorf("expected valid, got issues: %v", result.Issues)
	}
}

func TestValidateTypeMismatch(t *testing.T) {
	doc := parseDoc(t, `name = "test"`)
	schema := &validate.Schema{
		Types: map[string]string{
			"name": "integer",
		},
	}

	result := validate.Validate(doc, schema)
	if result.Valid {
		t.Error("expected invalid due to type mismatch")
	}
}

func TestValidateForbidden(t *testing.T) {
	doc := parseDoc(t, `
name = "test"
secret = "hidden"
`)
	schema := &validate.Schema{
		Forbidden: []string{"secret"},
	}

	result := validate.Validate(doc, schema)
	if result.Valid {
		t.Error("expected invalid due to forbidden field")
	}
}

func TestValidateMaxDepth(t *testing.T) {
	doc := parseDoc(t, `
[a.b.c]
  val = 1
`)
	schema := &validate.Schema{
		MaxDepth: 2,
	}

	result := validate.Validate(doc, schema)
	if len(result.Issues) == 0 {
		t.Errorf("expected depth warning, got none")
	}
}

func TestValidateSyntax(t *testing.T) {
	result := validate.ValidateSyntax(`
name = "test"
port = 8080
`)
	if !result.Valid {
		t.Errorf("expected valid syntax, got issues: %v", result.Issues)
	}
}

func TestSeverityString(t *testing.T) {
	tests := []struct {
		s    validate.Severity
		want string
	}{
		{validate.SeverityError, "error"},
		{validate.SeverityWarning, "warning"},
		{validate.SeverityInfo, "info"},
	}
	for _, tt := range tests {
		if got := tt.s.String(); got != tt.want {
			t.Errorf("Severity.String() = %q, want %q", got, tt.want)
		}
	}
}

func TestFormatIssues(t *testing.T) {
	doc := parseDoc(t, `name = "test"`)
	schema := &validate.Schema{
		Required: []string{"port"},
	}

	result := validate.Validate(doc, schema)
	text := validate.FormatIssues(result)
	if len(text) == 0 {
		t.Error("expected non-empty format output")
	}
}
