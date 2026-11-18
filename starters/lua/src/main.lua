package.path = "src/?.lua;" .. package.path

local starter = require("starter")
print(starter.greet("Lua"))
