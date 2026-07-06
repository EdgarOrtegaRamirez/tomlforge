package models_test

import (
	"testing"
	"time"

	"github.com/EdgarOrtegaRamirez/tomlforge/internal/models"
)

func TestNewString(t *testing.T) {
	v := models.NewString("hello")
	if v.Type != models.TypeString {
		t.Errorf("expected TypeString, got %v", v.Type)
	}
	if v.Str != "hello" {
		t.Errorf("expected 'hello', got %q", v.Str)
	}
}

func TestNewInteger(t *testing.T) {
	v := models.NewInteger(42)
	if v.Type != models.TypeInteger {
		t.Errorf("expected TypeInteger, got %v", v.Type)
	}
	if v.Int != 42 {
		t.Errorf("expected 42, got %d", v.Int)
	}
}

func TestNewFloat(t *testing.T) {
	v := models.NewFloat(3.14)
	if v.Type != models.TypeFloat {
		t.Errorf("expected TypeFloat, got %v", v.Type)
	}
	if v.Float != 3.14 {
		t.Errorf("expected 3.14, got %f", v.Float)
	}
}

func TestNewBool(t *testing.T) {
	v := models.NewBool(true)
	if v.Type != models.TypeBoolean {
		t.Errorf("expected TypeBoolean, got %v", v.Type)
	}
	if !v.Bool {
		t.Error("expected true")
	}
}

func TestNewDateTime(t *testing.T) {
	now := time.Now()
	v := models.NewDateTime(now)
	if v.Type != models.TypeDateTime {
		t.Errorf("expected TypeDateTime, got %v", v.Type)
	}
	if !v.Time.Equal(now) {
		t.Errorf("expected %v, got %v", now, v.Time)
	}
}

func TestNewArray(t *testing.T) {
	arr := []*models.Value{models.NewString("a"), models.NewString("b")}
	v := models.NewArray(arr)
	if v.Type != models.TypeArray {
		t.Errorf("expected TypeArray, got %v", v.Type)
	}
	if len(v.Array) != 2 {
		t.Errorf("expected 2 elements, got %d", len(v.Array))
	}
}

func TestNewTable(t *testing.T) {
	m := map[string]*models.Value{"key": models.NewString("value")}
	v := models.NewTable(m)
	if v.Type != models.TypeTable {
		t.Errorf("expected TypeTable, got %v", v.Type)
	}
	if len(v.Map) != 1 {
		t.Errorf("expected 1 key, got %d", len(v.Map))
	}
}

func TestAsString(t *testing.T) {
	v := models.NewString("hello")
	s, ok := v.AsString()
	if !ok || s != "hello" {
		t.Errorf("expected 'hello', got %q, %v", s, ok)
	}

	v2 := models.NewInteger(42)
	_, ok = v2.AsString()
	if ok {
		t.Error("expected false for non-string")
	}
}

func TestAsInt(t *testing.T) {
	v := models.NewInteger(42)
	n, ok := v.AsInt()
	if !ok || n != 42 {
		t.Errorf("expected 42, got %d, %v", n, ok)
	}
}

func TestAsFloat(t *testing.T) {
	v := models.NewFloat(3.14)
	f, ok := v.AsFloat()
	if !ok || f != 3.14 {
		t.Errorf("expected 3.14, got %f, %v", f, ok)
	}

	v2 := models.NewInteger(42)
	f2, ok := v2.AsFloat()
	if !ok || f2 != 42.0 {
		t.Errorf("expected 42.0, got %f, %v", f2, ok)
	}
}

func TestAsBool(t *testing.T) {
	v := models.NewBool(true)
	b, ok := v.AsBool()
	if !ok || !b {
		t.Errorf("expected true, got %v, %v", b, ok)
	}
}

func TestAsTime(t *testing.T) {
	now := time.Now()
	v := models.NewDateTime(now)
	T, ok := v.AsTime()
	if !ok || !T.Equal(now) {
		t.Errorf("expected %v, got %v, %v", now, T, ok)
	}
}

func TestAsArray(t *testing.T) {
	arr := []*models.Value{models.NewString("a")}
	v := models.NewArray(arr)
	a, ok := v.AsArray()
	if !ok || len(a) != 1 {
		t.Errorf("expected 1 element, got %d, %v", len(a), ok)
	}
}

func TestAsMap(t *testing.T) {
	m := map[string]*models.Value{"key": models.NewString("value")}
	v := models.NewTable(m)
	result, ok := v.AsMap()
	if !ok || len(result) != 1 {
		t.Errorf("expected 1 key, got %d, %v", len(result), ok)
	}
}

func TestString(t *testing.T) {
	tests := []struct {
		name     string
		value    *models.Value
		expected string
	}{
		{"string", models.NewString("hello"), `"hello"`},
		{"int", models.NewInteger(42), "42"},
		{"float", models.NewFloat(3.14), "3.14"},
		{"bool true", models.NewBool(true), "true"},
		{"bool false", models.NewBool(false), "false"},
		{"nil", nil, "<nil>"},
		{"empty", &models.Value{Type: models.TypeEmpty}, "<empty>"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.value.String(); got != tt.expected {
				t.Errorf("String() = %q, want %q", got, tt.expected)
			}
		})
	}
}

func TestEqual(t *testing.T) {
	tests := []struct {
		name     string
		a        *models.Value
		b        *models.Value
		expected bool
	}{
		{"both nil", nil, nil, true},
		{"one nil", models.NewString("a"), nil, false},
		{"same string", models.NewString("a"), models.NewString("a"), true},
		{"diff string", models.NewString("a"), models.NewString("b"), false},
		{"same int", models.NewInteger(1), models.NewInteger(1), true},
		{"diff int", models.NewInteger(1), models.NewInteger(2), false},
		{"diff type", models.NewString("1"), models.NewInteger(1), false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.a.Equal(tt.b); got != tt.expected {
				t.Errorf("Equal() = %v, want %v", got, tt.expected)
			}
		})
	}
}

func TestDocumentGetSetPath(t *testing.T) {
	doc := &models.Document{Root: make(map[string]*models.Value)}

	doc.SetPath("name", models.NewString("test"))
	if v := doc.GetPath("name"); v == nil || v.Str != "test" {
		t.Errorf("expected 'test', got %v", v)
	}

	doc.SetPath("server.port", models.NewInteger(8080))
	if v := doc.GetPath("server.port"); v == nil || v.Int != 8080 {
		t.Errorf("expected 8080, got %v", v)
	}

	if v := doc.GetPath("server.host"); v != nil {
		t.Errorf("expected nil, got %v", v)
	}
}

func TestDocumentDeletePath(t *testing.T) {
	doc := &models.Document{Root: make(map[string]*models.Value)}
	doc.SetPath("name", models.NewString("test"))
	doc.SetPath("age", models.NewInteger(25))

	if !doc.DeletePath("name") {
		t.Error("expected true")
	}
	if doc.GetPath("name") != nil {
		t.Error("expected nil after delete")
	}
	if doc.DeletePath("nonexistent") {
		t.Error("expected false for nonexistent")
	}
}

func TestDocumentKeys(t *testing.T) {
	doc := &models.Document{Root: make(map[string]*models.Value)}
	doc.SetPath("b", models.NewString("1"))
	doc.SetPath("a", models.NewString("2"))
	doc.SetPath("c", models.NewString("3"))

	keys := doc.Keys()
	if len(keys) != 3 {
		t.Errorf("expected 3 keys, got %d", len(keys))
	}
	if keys[0] != "a" || keys[1] != "b" || keys[2] != "c" {
		t.Errorf("expected [a b c], got %v", keys)
	}
}

func TestDocumentAllPaths(t *testing.T) {
	doc := &models.Document{Root: make(map[string]*models.Value)}
	doc.SetPath("name", models.NewString("test"))
	doc.SetPath("server.port", models.NewInteger(8080))

	paths := doc.AllPaths()
	if len(paths) != 3 {
		t.Errorf("expected 3 paths, got %d: %v", len(paths), paths)
	}
}

func TestDocumentFlatten(t *testing.T) {
	doc := &models.Document{Root: make(map[string]*models.Value)}
	doc.SetPath("name", models.NewString("test"))
	doc.SetPath("server.port", models.NewInteger(8080))

	flat := doc.Flatten()
	if len(flat) != 2 {
		t.Errorf("expected 2 flattened values, got %d", len(flat))
	}
	if v, ok := flat["server.port"]; !ok || v.Int != 8080 {
		t.Errorf("expected server.port=8080, got %v", v)
	}
}
