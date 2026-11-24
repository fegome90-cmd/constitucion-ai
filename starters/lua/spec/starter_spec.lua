package.path = "src/?.lua;" .. package.path

local starter = require("starter")

describe("starter.greet", function()
  it("saluda", function()
    assert.are.equal("Hola, Lua", starter.greet(" Lua "))
  end)
end)
