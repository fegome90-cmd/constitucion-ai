package greet

import "testing"

func TestHello(t *testing.T) {
	if got := Hello(" mundo "); got != "Hola, mundo" {
		t.Fatalf("Hello() = %q", got)
	}
}
