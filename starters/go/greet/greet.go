package greet

import "strings"

func Hello(name string) string {
	clean := strings.TrimSpace(name)
	if clean == "" {
		return "Hola, desconocido"
	}
	return "Hola, " + clean
}
