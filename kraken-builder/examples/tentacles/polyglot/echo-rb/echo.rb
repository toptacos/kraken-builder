require "json"
raw = STDIN.read
raw = "{}" if raw.nil? || raw.empty?
req = JSON.parse(raw)
print JSON.generate({
  "v" => 1, "id" => req["id"], "ok" => true,
  "result" => { "arm" => "echo-rb", "lang" => "ruby", "action" => req["action"], "echo" => req["payload"] || {} }
})
