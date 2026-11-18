"""API pública de ejemplo."""


def greet(name: str) -> str:
    """Devuelve un saludo determinista."""
    if not name.strip():
        raise ValueError("El nombre no puede estar vacío")
    return f"Hola, {name.strip()}"
