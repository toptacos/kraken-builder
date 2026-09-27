-- Chrome console extract. Reads one JSON line from stdin via argv env is awkward;
-- handler.sh only launches this when KRAKEN_CHROME=1.
on run
  set pageText to ""
  tell application "Google Chrome"
    if (count of windows) is 0 then
      make new window
    end if
    set pageText to execute front window's active tab javascript "document.body && document.body.innerText || ''"
  end tell
  set payload to "{\"v\":1,\"ok\":true,\"result\":{\"kind\":\"text\",\"value\":" & my jsonString(pageText) & ",\"meta\":{\"engine\":\"osascript\"}}}"
  return payload
end run

on jsonString(t)
  set t to my replace(t, "\\", "\\\\")
  set t to my replace(t, "\"", "\\\"")
  set t to my replace(t, return, "\\n")
  set t to my replace(t, linefeed, "\\n")
  return "\"" & t & "\""
end jsonString

on replace(t, a, b)
  set AppleScript's text item delimiters to a
  set bits to text items of t
  set AppleScript's text item delimiters to b
  set out to bits as text
  set AppleScript's text item delimiters to ""
  return out
end replace
