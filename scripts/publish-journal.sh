#!/bin/sh
# POST Kraken journal notes to blog.topta.co when BLOG_API_TOKEN is set.
# Never run seeders. Cloudflare-safe POST.
#
# Taxonomy: every post carries the internal-projects term for this repo,
# "project:kraken" (see docs/TAXONOMY.md and website/data/taxonomy.json).
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
    -d "{\"title\":\"$title\",\"slug\":\"$slug\",\"meta_description\":\"$desc\",\"category\":\"DevOps\",\"is_published\":true,\"tags\":[\"kraken\",\"cli\",\"homelab\",\"project:kraken\"],\"content\":$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$html")}" \
    >/dev/null && echo "ok $slug" || echo "fail $slug"
}

post kraken-cli-one-binary "Kraken CLI: one binary, many tentacles" \
  "Local CLI plugin runner. Install, demo, doctor." \
  "<h2>Local CLI plugin runner</h2><p><a href=\"https://kraken.topta.co/cli\">Install</a> then <code>kraken demo</code>.</p><pre>curl -fsSL https://kraken.topta.co/install.sh | sh</pre>"

post kraken-grants-default-deny "Kraken grants: default deny" \
  "kraken grant before expose, tunnel, llm, scourge. Self-hosted tentacle CLI." \
  "<h2>Default deny</h2><p>See <a href=\"https://kraken.topta.co/blog/grants-default-deny\">the journal</a>.</p><pre>kraken grant expose</pre>"

post kraken-why-kraken "Why Kraken beats the alternatives" \
  "A 0.4 MB local-first CLI plugin runner with a JSON contract any language can speak, measured against n8n, Zapier, Terraform, make, and agent CLIs." \
  "<h2>Smallest thing that does the job</h2><p>0.4 MB of core, one dependency (pyyaml, MIT). No daemon, no server, no account. <code>kraken demo</code> answers with the network unplugged.</p><h2>The contract, not a language</h2><p>The same tentacle in Python, Bash, Node, PHP, Ruby, Perl, and Go, all answering one command — verified in CI by <code>scripts/verify_articles.py</code>.</p><pre>sh       {\"lang\": \"sh\", \"id\": \"1\", \"ok\": true}
python   {\"lang\": \"python\", \"id\": \"1\", \"ok\": true}
node     {\"lang\": \"node\", \"id\": \"1\", \"ok\": true}
php      {\"lang\": \"php\", \"id\": \"1\", \"ok\": true}
ruby     {\"lang\": \"ruby\", \"id\": \"1\", \"ok\": true}
perl     {\"lang\": \"perl\", \"id\": \"1\", \"ok\": true}
go       {\"lang\": \"go\", \"id\": \"1\", \"ok\": true}</pre><h2>Safe by default</h2><p>Exposure is default-deny: <code>{\"ok\": false, \"result\": {\"error\": \"grant expose first: kraken grant expose\"}}</code> until a human grants it, and the bind is <code>127.0.0.1</code>.</p><h2>And honest about losing</h2><p>One interpreter per run means <code>kraken run</code> loses to C <em>make</em> on raw speed (330 ms vs 28 ms measured). Use make for one shell line; use Kraken when it becomes a plugin someone else ships.</p><p><a href=\"https://kraken.topta.co/compare.html\">Full comparison with benchmarks →</a></p>"

echo "done. Check blog.topta.co DevOps."
