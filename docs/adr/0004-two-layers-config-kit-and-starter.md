# Dos capas: config kit y starter

Status: accepted

El repo mantiene dos capas separadas. `templates/<lenguaje>/` contiene solo archivos de configuración y es la fuente de verdad de los config kits. `starters/<lenguaje>/` contiene un proyecto ejecutable de ejemplo, tomado del ZIP auditado del 17 de noviembre de 2026, que sirve como fixture de los smoke tests y como punto de partida del generador opcional.

El ZIP original mezclaba ambas cosas en un solo directorio, lo que hacía imposible aplicar la configuración a un proyecto existente sin arrastrar código de ejemplo. Separarlas preserva la definición de config kit y permite importar los diez starters sin modificar los dos kits ya construidos.

Consecuencia: cada versión y cada pin se declaran una sola vez, en el config kit; el starter los consume. Para los descriptores indexados en `catalog.json`, el starter apunta al archivo canónico con un enlace simbólico relativo. Los lockfiles registran resoluciones y viven en el starter. El scaffolder exporta los descriptores como archivos regulares junto a esos lockfiles. El verificador exige el enlace incluso si una copia local tiene el mismo contenido.
