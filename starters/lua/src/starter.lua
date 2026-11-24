local M = {}

function M.greet(name)
  assert(type(name) == "string", "name debe ser un string")
  local clean = name:match("^%s*(.-)%s*$")
  if clean == "" then
    return "Hola, desconocido"
  end
  return "Hola, " .. clean
end

return M
