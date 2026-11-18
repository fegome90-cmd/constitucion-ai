# Config kit: Java

Kit mínimo y reproducible para proyectos Java (`>=21`) con Maven (`>=3.9`). La capa ejecutable está en `starters/java/` y el contrato de comandos en `catalog.json` (ADR-0004). Los pins se declaran una sola vez, acá.

## Categorías incluidas

| Categoría | Herramienta | Versión |
| --- | --- | --- |
| Gestor de dependencias / build | Maven (`pom.xml`) | >=3.9 |
| Formatter | Spotless + `google-java-format` | 3.10.3 / 2.0.0 |
| Linter | `mvn spotless:check` | 3.10.3 |
| Type-checker / compilador | `maven-compiler-plugin` (`release 21`) | 3.14.1 |
| Test runner | JUnit Jupiter + `maven-surefire-plugin` | 6.0.0 / 3.5.4 |

## Excluidos deliberadamente

- **Checkstyle / SpotBugs / PMD**: quedan fuera del núcleo mínimo para evitar reglas duplicadas sobre Spotless y `javac`; pueden sumarse por proyecto si se requiere análisis adicional.
- **Maven Wrapper (`mvnw`)**: no se distribuyen binarios generados sin procedencia verificada; puede inicializarse con `mvn -N wrapper:wrapper` en un entorno conectado.

## Uso

Aplicar el kit a un directorio sin `pom.xml` previo con el script del repo:

```bash
scripts/apply-kit.sh java <destino>
```

El script normaliza `<artifactId>starter-java</artifactId>` a `<artifactId>java-config-kit-project</artifactId>`, conserva los pins de Maven y JUnit, omite `README.md` y `EVIDENCE.md`, y corre el smoke test (`mvn spotless:check verify`). Para combinarlo con herramientas transversales, aplicar también `_common`.

Los detalles de adopción y la excepción de `maven-compiler-plugin` y `maven-surefire-plugin` están en `EVIDENCE.md`.
