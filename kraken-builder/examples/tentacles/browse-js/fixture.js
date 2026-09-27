#!/usr/bin/env node
const fs = require("fs");
let raw = "";
process.stdin.on("data", (c) => { raw += c; });
process.stdin.on("end", () => {
  const req = JSON.parse(raw || "{}");
  const p = req.payload || {};
  const action = req.action || "fetch";
  const ok = (result) => {
    process.stdout.write(JSON.stringify({ v: 1, id: req.id, ok: true, result }));
  };
  if (action === "finish") {
    const rawBody = p.raw || {};
    const patch = p.patch || {};
    const text = (rawBody.value || rawBody.text || "fixture page");
    const dest = patch.value || p.path || "/tmp/kraken-browse.txt";
    try { fs.writeFileSync(dest, String(text)); } catch (e) { /* still report */ }
    ok({
      kind: "file",
      value: dest,
      meta: { bytes: String(text).length, source: rawBody.meta && rawBody.meta.url },
      finished: true,
    });
    return;
  }
  const url = p.url || "https://example.com";
  ok({
    kind: "text",
    value: "Example Domain\nThis domain is for use in illustrative examples.",
    meta: { url, title: "Example Domain", engine: "fixture" },
  });
});
