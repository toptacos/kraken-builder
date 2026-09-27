const fs = require("fs");
const req = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
const name = (req.payload && req.payload.name) || "world";
process.stdout.write(JSON.stringify({
  v: 1, id: req.id, ok: true,
  result: { arm: "hello-js", lang: "javascript", hello: `hello, ${name}` },
}));
