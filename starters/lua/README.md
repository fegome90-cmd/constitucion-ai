# Lua · LuaRocks + StyLua + LuaLS + Busted

Lua 5.4. Busted es el runner; StyLua el formateador; LuaLS apoya el diagnóstico de editor.

```sh
luarocks install busted
# instalar StyLua por release oficial o gestor de paquetes
stylua --check src spec
busted
lua src/main.lua
```

Lua 5.5 queda fuera de este núcleo hasta comprobar soporte completo del formateador. `Luacheck` se puede añadir como gate opcional tras verificar compatibilidad. Este proyecto no fuerza un lockfile inexistente.

Control integrado: `stylua --check src spec && busted`.
