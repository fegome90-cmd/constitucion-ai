import { readFileSync } from "node:fs";
import { createServer } from "node:http";

const fixture = readFileSync(
  new URL("../fixtures/index.html", import.meta.url),
);
const port = Number(process.env.PORT ?? "4173");
const server = createServer((request, response) => {
  if (request.url !== "/") {
    response.writeHead(404).end("No encontrado");
    return;
  }
  response
    .writeHead(200, { "Content-Type": "text/html; charset=utf-8" })
    .end(fixture);
});
server.listen(port, "127.0.0.1", () => {
  console.log(`Fixture: http://127.0.0.1:${port}`);
});
