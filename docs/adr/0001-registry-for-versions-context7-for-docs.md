# Registry para versiones, Context7 para documentación

Status: accepted

Los config kits fijan números de versión desde el registry autoritativo de cada ecosistema (PyPI JSON API, npm registry, crates.io API, GitHub Releases), no desde Context7. Context7 se usa para escribir la sintaxis de configuración en esa versión ya elegida y como señal de que la herramienta tiene documentación vigente.

El pedido original era que todas las herramientas "trabajen de la mano de Context7 para definir versiones". Verificado el 2026-11-17: Context7 es un recuperador de documentación, sin datos de registry, sin campo de versión "latest" (`version=latest` es documentado como equivalente a no pasar versión) y sin detección de yanked. Una consulta empírica devolvió texto no estructurado que incluía una prerelease de la rama canary. Fijar un número inferido de un snippet de docs puede clavarse en una versión inexistente, prerelease o incompatible.

Considered Options:

- **Registry + Context7 (elegido)**: número desde el registry, sintaxis desde Context7.
- **Context7 como oráculo**: rechazado — Wrong data class, indexado parcial y texto no estructurado.
- **Sin fijar (mínimos)**: rechazado — sacrifica reproducibilidad, que es justo lo que un kit busca.
