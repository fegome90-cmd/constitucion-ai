# Config kits como archivos estáticos, no como scaffolder

Status: superseded by ADR-0005

Cada config kit es un conjunto de archivos reales y versionados bajo `templates/<lenguaje>/`, con un script bash delgado (`apply-kit.sh <lang> <destino>`) que copia los archivos y corre el smoke test. Se descartó copier/cookiecutter y cualquier generador con estado.

Los archivos son la fuente de verdad y son legibles y testeables sin ejecutar nada. Un scaffolder agrega una capa de indirección y dependencias para un conjunto de archivos que, por diseño, es chico. Las herramientas transversales del repo (markdownlint, yamllint, shellcheck, codespell) viven en `templates/_common/` para mantener el mínimo de cada lenguaje limpio.

Consecuencia: el kit Python se extrae de la configuración existente del repo; los otros siete lenguajes se construyen con research, porque no hay fuente local.
