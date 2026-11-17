/// Genera un saludo sin efectos laterales.
pub fn greet(name: &str) -> String {
    let trimmed = name.trim();
    if trimmed.is_empty() {
        return "Hola, desconocido".to_string();
    }
    format!("Hola, {trimmed}")
}

#[cfg(test)]
mod tests {
    use super::greet;

    #[test]
    fn greets() {
        assert_eq!(greet(" mundo "), "Hola, mundo");
    }
}
