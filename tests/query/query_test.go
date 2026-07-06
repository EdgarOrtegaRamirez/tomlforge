package query_test

import (
	"testing"

	"github.com/EdgarOrtegaRamirez/tomlforge/internal/models"
	"github.com/EdgarOrtegaRamirez/tomlforge/internal/parser"
	"github.com/EdgarOrtegaRamirez/tomlforge/internal/query"
)

func setupDoc(t *testing.T) *models.Document {
	t.Helper()
	input := `
name = "test"
port = 8080

[server]
host = "localhost"
port = 3000

[database]
driver = "postgres"
connections = 10
`
	p := parser.New()
	doc, err := p.Parse(input)
	if err != nil {
		t.Fatalf("failed to parse: %v", err)
	}
	return doc
}

func TestGetSimple(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	v := q.Get("name")
	if v == nil || v.Str != "test" {
		t.Errorf("expected name='test', got %v", v)
	}
}

func TestGetNested(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	v := q.Get("server.host")
	if v == nil || v.Str != "localhost" {
		t.Errorf("expected server.host='localhost', got %v", v)
	}
}

func TestGetNonExistent(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	v := q.Get("nonexistent")
	if v != nil {
		t.Errorf("expected nil, got %v", v)
	}
}

func TestGetString(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	s, err := q.GetString("name")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if s != "test" {
		t.Errorf("expected 'test', got %q", s)
	}
}

func TestGetInt(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	n, err := q.GetInt("port")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if n != 8080 {
		t.Errorf("expected 8080, got %d", n)
	}
}

func TestGetTable(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	m, err := q.GetTable("server")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(m) != 2 {
		t.Errorf("expected 2 keys, got %d", len(m))
	}
}

func TestHas(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	if !q.Has("name") {
		t.Error("expected name to exist")
	}
	if q.Has("nonexistent") {
		t.Error("expected nonexistent to not exist")
	}
	if !q.Has("server.host") {
		t.Error("expected server.host to exist")
	}
}

func TestAllPaths(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	paths := q.AllPaths()
	if len(paths) < 5 {
		t.Errorf("expected at least 5 paths, got %d: %v", len(paths), paths)
	}
}

func TestSearch(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	results := q.Search("test")
	if len(results) == 0 {
		t.Error("expected non-empty results")
	}
}

func TestSelect(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	results := q.Select("name", "port")
	if len(results) != 2 {
		t.Errorf("expected 2 results, got %d", len(results))
	}
}

func TestTypeOf(t *testing.T) {
	doc := setupDoc(t)
	q := query.New(doc)

	if q.TypeOf("name") != "string" {
		t.Errorf("expected string type, got %s", q.TypeOf("name"))
	}
	if q.TypeOf("nonexistent") != "not_found" {
		t.Errorf("expected not_found, got %s", q.TypeOf("nonexistent"))
	}
}

func TestLen(t *testing.T) {
	doc, _ := parser.New().Parse(`items = [1, 2, 3]`)
	q := query.New(doc)

	n, err := q.Len("items")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if n != 3 {
		t.Errorf("expected 3, got %d", n)
	}
}

func TestSortedKeys(t *testing.T) {
	input := `
[b]
z = 1
a = 2
m = 3
`
	doc, _ := parser.New().Parse(input)
	q := query.New(doc)

	keys, err := q.SortedKeys("b")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(keys) != 3 {
		t.Errorf("expected 3 keys, got %d", len(keys))
	}
	if keys[0] != "a" || keys[1] != "m" || keys[2] != "z" {
		t.Errorf("expected [a m z], got %v", keys)
	}
}

func TestIndexAccess(t *testing.T) {
	doc, _ := parser.New().Parse(`arr = [10, 20, 30]`)
	q := query.New(doc)

	v, err := q.IndexAccess("arr", 1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if v == nil || v.Int != 20 {
		t.Errorf("expected 20, got %v", v)
	}

	_, err = q.IndexAccess("arr", 10)
	if err == nil {
		t.Error("expected error for out of bounds")
	}
}
