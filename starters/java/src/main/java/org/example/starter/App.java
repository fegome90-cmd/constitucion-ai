package org.example.starter;

public final class App {
  private App() {}

  public static String greet(String name) {
    if (name == null || name.isBlank()) {
      throw new IllegalArgumentException("El nombre no puede estar vacío");
    }
    return "Hola, " + name.strip();
  }

  public static void main(String[] args) {
    System.out.println(greet("Java"));
  }
}
