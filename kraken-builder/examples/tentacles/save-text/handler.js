#!/usr/bin/env node
const os = require("os");
const path = require("path");
let raw = "";
process.stdin.on("data", (c) => { raw += c; });
process.stdin.on("end", () => {
  const req = JSON.parse(raw || "{}");
  const p = req.payload || {};
  const blob = p.result || {};
  const inner = blob.result && typeof blob.result === "object" ? blob.result : blob;
  const text = inner.value || inner.text || "";
  const dest = path.join(os.tmpdir(), "kraken-browse.txt");
  const patch = {
    kind: "file",
    value: dest,
    meta: { bytes: String(text).length, from: inner.kind || "text" },
  };
  process.stdout.write(JSON.stringify({
    v: 1,
    id: req.id,
    ok: true,
    result: { patch, target: p.target },
  }));
});
