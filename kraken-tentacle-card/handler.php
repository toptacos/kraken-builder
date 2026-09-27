<?php
declare(strict_types=1);
const PROTOCOL = 1;
const VERSION = "0.1.0";

function home(): string {
    $h = getenv("KRAKEN_HOME") ?: (getenv("HOME") ?: sys_get_temp_dir());
    return $h . "/.kraken/data/card";
}

function out(array $body): void {
    echo json_encode($body, JSON_UNESCAPED_SLASHES), "\n";
}

function ok($id, array $result): void {
    out(["v" => PROTOCOL, "id" => $id, "ok" => true, "result" => $result]);
}

function err($id, string $code, string $msg): void {
    out(["v" => PROTOCOL, "id" => $id, "ok" => false, "error" => ["code" => $code, "message" => $msg]]);
}

function h(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, "UTF-8");
}

function render_html(array $p): string {
    $title = $p["title"] ?? "card";
    $body = $p["body"] ?? $p["text"] ?? "";
    $meta = $p["meta"] ?? "local";
    return "<!doctype html><meta charset=utf-8>"
        . "<body style='margin:0;background:#0B1220;color:#E7F6F6;font-family:sans-serif;padding:48px'>"
        . "<p style='color:#2FD0C6;letter-spacing:.2em;text-transform:uppercase;font-size:12px'>kraken · card</p>"
        . "<h1>" . h((string)$title) . "</h1>"
        . "<p>" . nl2br(h((string)$body)) . "</p>"
        . "<p style='color:#e7c56a'>" . h((string)$meta) . "</p></body>";
}

$raw = stream_get_contents(STDIN);
$req = $raw ? json_decode($raw, true) : ["action" => "ping"];
if (!is_array($req)) {
    err(null, "bad_json", "invalid json");
    exit(0);
}
$action = $req["action"] ?? "ping";
$id = $req["id"] ?? null;
$p = $req["payload"] ?? [];
if (!is_array($p)) $p = [];

switch ($action) {
    case "":
    case "ping":
        ok($id, ["arm" => "card", "version" => VERSION, "protocol" => PROTOCOL, "runtime" => "php"]);
        break;
    case "render":
        ok($id, ["arm" => "card", "html" => render_html($p)]);
        break;
    case "write":
        $dir = home();
        if (!is_dir($dir) && !mkdir($dir, 0700, true) && !is_dir($dir)) {
            err($id, "io", "cannot create data dir");
            break;
        }
        $path = $dir . "/card.html";
        file_put_contents($path, render_html($p));
        chmod($path, 0600);
        ok($id, ["arm" => "card", "path" => $path]);
        break;
    case "finish":
        $rawp = $p["raw"] ?? ["arm" => "card"];
        if (!is_array($rawp)) $rawp = ["arm" => "card"];
        $patch = $p["patch"] ?? [];
        if (is_array($patch)) $rawp = array_merge($rawp, $patch);
        $rawp["finished"] = true;
        ok($id, $rawp);
        break;
    case "clear":
        $path = home() . "/card.html";
        if (is_file($path)) unlink($path);
        ok($id, ["cleared" => true]);
        break;
    default:
        err($id, "unknown_action", "unknown action " . $action);
}
