-- Kraken Chrome ops. Profile Default = matt@topta.co.
-- argv: url, javascript
on run argv
  set targetUrl to item 1 of argv
  set js to item 2 of argv
  tell application "Google Chrome"
    activate
    if (count of windows) is 0 then make new window
    set URL of active tab of front window to targetUrl
    delay 3
    set resultText to execute front window's active tab javascript js
  end tell
  return resultText
end run
