# Polyglot: one contract, six languages

*The same tentacle, written six ways. Every block on this page was executed by
`scripts/verify_articles.py` on a machine with no network — including the
`go run` one, which compiles a program before answering.*

## Why a contract instead of a runtime

Most plugin systems pick a language for you. Node for n8n, Python for pytest
plugins, Go for Terraform providers. Kraken picks the *interface* instead:
one JSON object on stdin, one JSON object on stdout, exit 0.

That choice has one consequence worth internalizing: **the tentacle owns its
runtime**. Core shells out and gets out of the way. `pyyaml` is the only
dependency Kraken itself has; your tentacle's dependencies are your
tentacle's business — vendored, containerized, or none at all.

```
 your language    kraken core        your language
 (reads stdin, ── one envelope ──▶  (any process)
  writes stdout)
```

## The file-per-language rule

Core maps a file extension to an interpreter and nothing else:

| Extension | Runs as | Needs installed |
|---|---|---|
| `.py` | `python3 <handler>` | python 3.11+ |
| `.sh` | `bash <handler>` | bash |
| `.js`, `.mjs` | `node <handler>` | node |
| `.php` | `php <handler>` | php |
| `.rb` | `ruby <handler>` | ruby |
| `.pl` | `perl <handler>` | perl |
| `.go` | `go run <handler>` | go |
| anything else | executed directly | its own shebang |

No SDK, no bindings, no lockfile. If your language can read stdin and print
JSON, it is on that list by construction.

## Build them all

Each tentacle is the same five-line program: read the envelope, answer with
the language you were written in. Availability is probed first, so on a box
without php you will see `php: not installed` rather than a failure — the
article and the contract both degrade honestly. For the same reason the
output blocks below are marked `output,vary`: the verifier still executes
every command and records what printed on this machine, but the exact set
of languages is yours, not everyone's.

```run,sh
mk() {  # mk <name> <file>
  mkdir -p "echo-$1"
  cat > "echo-$1/tentacle.yaml" <<EOF
name: echo-$1
version: 0.1.0
license: free
runtime: binary
binary: $2
actions: [ping]
description: The same tentacle in $1.
EOF
}

mk sh handler.sh
cat > echo-sh/handler.sh <<'EOF'
#!/bin/sh
set -eu
exec python3 -c '
import json, sys
req = json.load(sys.stdin)
sys.stdout.write(json.dumps({"lang": "sh", "id": req.get("id"), "ok": True}))
'
EOF
chmod +x echo-sh/handler.sh

mk python handler.py
cat > echo-python/handler.py <<'EOF'
import json, sys

req = json.load(sys.stdin)
sys.stdout.write(json.dumps({"lang": "python", "id": req.get("id"), "ok": True}))
EOF

mk node handler.js
cat > echo-node/handler.js <<'EOF'
let req = "";
process.stdin.on("data", (c) => (req += c));
process.stdin.on("end", () => {
  const parsed = JSON.parse(req || "{}");
  process.stdout.write(JSON.stringify({ lang: "node", id: parsed.id, ok: true }));
});
EOF

if command -v php >/dev/null 2>&1; then
  mk php handler.php
  cat > echo-php/handler.php <<'EOF'
<?php
$req = json_decode(stream_get_contents(STDIN) ?: "{}", true);
echo json_encode(["lang" => "php", "id" => $req["id"] ?? null, "ok" => true]);
EOF
else
  echo "php: not installed, skipped"
fi

if command -v ruby >/dev/null 2>&1; then
  mk ruby handler.rb
  cat > echo-ruby/handler.rb <<'EOF'
require "json"
raw = STDIN.read
req = raw.empty? ? {} : JSON.parse(raw)
puts JSON.generate({ lang: "ruby", id: req["id"], ok: true })
EOF
else
  echo "ruby: not installed, skipped"
fi

if command -v perl >/dev/null 2>&1; then
  mk perl handler.pl
  cat > echo-perl/handler.pl <<'EOF'
use strict; use warnings; use JSON::PP;
my $raw = do { local $/; <STDIN> };
my $req = decode_json($raw eq "" ? "{}" : $raw);
# canonical sorts keys: Perl randomizes hash order per process
# (PERL_HASH_SEED), so the plain encode would answer with the same data in
# a different order every run.
print JSON::PP->new->canonical->encode({ lang => "perl", id => $req->{id}, ok => JSON::PP::true });
EOF
else
  echo "perl: not installed, skipped"
fi

if command -v go >/dev/null 2>&1; then
  mk go handler.go
  # `go run` compiles before answering; the manifest may ask for more than
  # core's 30s default, clamped to a 300s ceiling.
  printf 'timeout_sec: 120\n' >> echo-go/tentacle.yaml
  cat > echo-go/handler.go <<'EOF'
package main

import (
	"encoding/json"
	"os"
)

func main() {
	var req map[string]any
	json.NewDecoder(os.Stdin).Decode(&req)
	resp := map[string]any{"lang": "go", "ok": true}
	if id, ok := req["id"]; ok {
		resp["id"] = id
	}
	json.NewEncoder(os.Stdout).Encode(resp)
}
EOF
else
  echo "go: not installed, skipped"
fi

mkdir -p echo-fold
cat > echo-fold/tentacle.yaml <<EOF
name: echo-fold
version: 0.1.0
license: free
runtime: binary
binary: handler.py
actions: [ping]
description: Echoes back the payload it was handed.
EOF
cat > echo-fold/handler.py <<'PY'
import json, sys

req = json.load(sys.stdin)
langs = (req.get("payload") or {}).get("langs") or {}
sys.stdout.write(json.dumps({
    "v": 1,
    "id": req.get("id"),
    "ok": True,
    "result": {
        "lang": "fold",
        "received": sorted(langs),
        "answers": langs,
    },
}))
PY

for d in echo-*; do python3 -m kraken tentacle add "$d" >/dev/null 2>&1 && echo "installed $d"; done
```

```output,vary
installed echo-fold
installed echo-go
installed echo-node
installed echo-perl
installed echo-php
installed echo-python
installed echo-ruby
installed echo-sh
```

## Run them all

The loop is the point: identical command, identical contract, five different
runtimes answering:

```run,sh
for d in echo-sh echo-python echo-node echo-php echo-ruby echo-perl echo-go; do
  [ -d "$d" ] || continue
  printf '%-12s ' "${d#echo-}"
  python3 -m kraken run "$d" ping
done
```

```output,vary
sh           {"lang": "sh", "id": "1", "ok": true}
python       {"lang": "python", "id": "1", "ok": true}
node         {"lang": "node", "id": "1", "ok": true}
php          {"lang": "php", "id": "1", "ok": true}
ruby         {"lang": "ruby", "id": "1", "ok": true}
perl         {"id": "1", "lang": "perl", "ok": true}
go           {"id": "1", "lang": "go", "ok": true}
```

## The one that compiles

`go run` is not a typo: a Go tentacle is a source file that `go` compiles
and executes on every invocation. The first run pays the toolchain; the ones
after it hit the build cache. Run it twice and the answers are identical —
which is the part you were promised:

```run,sh
if [ -d echo-go ]; then
  python3 -m kraken run echo-go ping
  python3 -m kraken run echo-go ping
else
  echo "go: not installed on this machine, nothing to compile"
fi
```

```output,vary
{"id": "1", "lang": "go", "ok": true}
{"id": "1", "lang": "go", "ok": true}
```

## One workflow, all of them at once

A tentacle is not just individually runnable — the workflow runner fans out
across them in parallel and folds the answers into one object:

```run,sh
RUNNERS="echo-sh echo-python"
for extra in echo-node echo-php echo-ruby echo-perl echo-go; do
  [ -d "$extra" ] && RUNNERS="$RUNNERS $extra"
done

{
  echo "name: polyglot-ping"
  echo "goal: The same ping in every installed language."
  echo "steps:"
  echo "  - id: fanout"
  echo "    parallel:"
  for r in $RUNNERS; do
    echo "      - id: ${r#echo-}"
    echo "        tentacle: $r"
    echo "        action: ping"
  done
  echo "  - id: fold"
  echo "    tentacle: echo-fold"
  echo "    action: ping"
  echo "    payload:"
  echo "      langs: \$fanout"
} > goal.yaml

python3 -m kraken workflow run goal.yaml | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('workflow ok:', data['ok'])
fold = data['results']['fold']['result']
print('fold received', len(fold['received']), 'language answers:')
for lang in fold['received']:
    answer = fold['answers'][lang]
    print(' ', lang, '->', answer['lang'], 'ok=' + str(answer['ok']))
"
```

```output,vary
workflow ok: True
fold received 7 language answers:
  go -> go ok=True
  node -> node ok=True
  perl -> perl ok=True
  php -> php ok=True
  python -> python ok=True
  ruby -> ruby ok=True
  sh -> sh ok=True
```

`payload: {langs: $fanout}` is the interpolation: the fold step's payload
*is* the parallel group's answers, keyed by step id. Each value is that
tentacle's own response object — `lang` is the language, not a wrapper —
which is why the fold handler can index straight into it.

## What this bought you

Five languages, one `tentacle.yaml` shape each, no SDK, no plugin host, and
no daemon: `kraken add` copies files, `kraken run` execs a process. A
tentacle you write in bash today can be rewritten in Rust tomorrow without
touching the caller — the contract is the API.

Every command and output above was executed by `scripts/verify_articles.py`
in an isolated `KRAKEN_HOME` with `KRAKEN_OFFLINE=1`.
