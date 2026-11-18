export function title(label: string): string {
  const trimmed = label.trim();
  if (!trimmed) throw new Error("Falta el título");
  return trimmed;
}
