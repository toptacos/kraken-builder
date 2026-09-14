require "json"
raw = STDIN.read
raw = "{}" if raw.nil? || raw.empty?
req = JSON.parse(raw)
name = (((req["payload"] || {})["name"]) || "world")
print({ v: 1, id: req["id"], ok: true, result: { arm: "hello-rb", lang: "ruby", hello: "hello, #{name}" } }.to_json)
