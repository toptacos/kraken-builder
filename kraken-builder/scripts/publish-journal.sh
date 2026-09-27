#!/bin/sh
# POST Kraken journal notes to blog.topta.co when BLOG_API_TOKEN is set.
# Never run seeders. Cloudflare-safe POST.
set -eu
API="${BLOG_API_URL:-https://api.topta.co}"
TOKEN="${BLOG_API_TOKEN:-}"
if [ -z "$TOKEN" ]; then
  echo "skip: set BLOG_API_TOKEN (Sanctum). Drafts live at https://kraken.topta.co/blog"
  exit 0
fi
post() {
  slug="$1"
  title="$2"
  desc="$3"
  html="$4"
  curl -fsS -X POST "$API/api/v1/blog/posts" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"$title\",\"slug\":\"$slug\",\"meta_description\":\"$desc\",\"category\":\"DevOps\",\"is_published\":true,\"tags\":[\"kraken\",\"cli\",\"homelab\"],\"content\":$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$html")}" \
    >/dev/null && echo "ok $slug" || echo "fail $slug"
}

post kraken-cli-one-binary "Kraken CLI: one binary, many tentacles" \
  "Local CLI plugin runner. Install, demo, doctor." \
  "<h2>Local CLI plugin runner</h2><p><a href=\"https://kraken.topta.co/cli\">Install</a> then <code>kraken demo</code>.</p><pre>curl -fsSL https://kraken.topta.co/install.sh | sh</pre>"

post kraken-grants-default-deny "Kraken grants: default deny" \
  "kraken grant before expose, tunnel, llm, scourge. Self-hosted tentacle CLI." \
  "<h2>Default deny</h2><p>See <a href=\"https://kraken.topta.co/blog/grants-default-deny\">the journal</a>.</p><pre>kraken grant expose</pre>"

echo "done. Check blog.topta.co DevOps."
