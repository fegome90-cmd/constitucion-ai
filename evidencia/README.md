# Evidencia

`sha256-archivos.txt` es la huella **inmutable del ZIP original** del 17 de noviembre de 2026. Sus rutas son relativas a la raíz de ese ZIP (`templates/...`), no a la raíz de este repo: acá ese mismo árbol se llama `starters/`. No se regenera ni se edita; es prueba de procedencia.

El estado final del repo se registra aparte en `MANIFEST.current.sha256`, que se genera recién al cerrar la integración (F5), después de todas las modificaciones.

`auditoria.json` y `entorno.txt` describen el entorno del laboratorio original, no el de este repo. La auditoria de acá se regenera en F5 con los gates efectivamente ejecutados.
