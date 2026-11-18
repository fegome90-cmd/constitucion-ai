export function greet(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) {
    throw new Error("El nombre no puede estar vacío");
  }
  return `Hola, ${trimmed}`;
}
