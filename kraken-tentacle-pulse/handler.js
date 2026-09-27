#!/usr/bin/env node
"use strict";

const fs = require("fs");

function readStdin() {
  try {
    return fs.readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

function ok(id, result) {
  send({ v: 1, id, ok: true, result });
}

function err(id, code, message) {
  send({ v: 1, id, ok: false, error: { code, message } });
}

const raw = readStdin().trim();
let req;
try {
  req = raw ? JSON.parse(raw) : { action: "ping", payload: {} };
} catch (e) {
  err(null, "bad_json", String(e.message || e));
  process.exit(0);
}

const action = req.action || "ping";
const id = req.id ?? null;
const p = req.payload && typeof req.payload === "object" ? req.payload : {};

function isEnvelope(x) {
  return x && typeof x === "object" && Number(x.v) === 1 && typeof x.ok === "boolean";
}

switch (action) {
  case "ping":
    ok(id, { arm: "pulse", version: "0.1.0", protocol: 1, runtime: "javascript" });
    break;
  case "check": {
    const target = p.envelope || p;
    const valid = isEnvelope(target);
    ok(id, {
      arm: "pulse",
      valid,
      hasError: !!(target && target.error),
      keys: target && typeof target === "object" ? Object.keys(target) : [],
    });
    break;
  }
  case "wrap": {
    const result = p.result && typeof p.result === "object" ? p.result : { note: p.note || "wrapped" };
    result.arm = result.arm || "pulse";
    ok(id, result);
    break;
  }
  case "finish": {
    const rawp = Object.assign({ arm: "pulse" }, p.raw || {}, p.patch || {}, { finished: true });
    ok(id, rawp);
    break;
  }
  default:
    err(id, "unknown_action", "unknown action " + action);
}
