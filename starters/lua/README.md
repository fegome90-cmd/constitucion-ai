# Lua · LuaRocks + StyLua + LuaLS + Busted

Lua 5.4. Busted es el runner; StyLua el formateador; LuaLS apoya el diagnóstico de editor.

```sh
version=$(sed -n 's/^busted==//p' rocks.txt)
luarocks --lua-version=5.4 --local install busted "${version:?}"
# Instalar la versión de StyLua indicada en rocks.txt y habilitar los binarios de LuaRocks.
stylua src spec
stylua --check src spec
busted
lua src/main.lua
```

Lua 5.5 queda fuera de este núcleo hasta comprobar soporte completo del formateador. `Luacheck` se puede añadir como gate opcional tras verificar compatibilidad. Este proyecto no fuerza un lockfile inexistente.

Control integrado (`check`): `stylua --check src spec && busted`.
