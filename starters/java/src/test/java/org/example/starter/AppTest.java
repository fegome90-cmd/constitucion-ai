package org.example.starter;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

class AppTest {
  @Test
  void saysHello() {
    assertEquals("Hola, Java", App.greet(" Java "));
  }

  @Test
  void rejectsBlank() {
    assertThrows(IllegalArgumentException.class, () -> App.greet(" "));
  }
}
