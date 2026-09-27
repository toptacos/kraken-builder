const fs = require("fs");
const req = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
process.stdout.write(JSON.stringify({
  v: 1, id: req.id, ok: true,
  result: { arm: "echo-js", lang: "javascript", action: req.action, echo: req.payload || {} }
}));
