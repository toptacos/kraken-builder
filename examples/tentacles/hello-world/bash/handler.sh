#!/usr/bin/env bash
req=$(cat)
id=$(printf '%s' "$req" | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
name=$(printf '%s' "$req" | sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
[ -z "$name" ] && name=world
printf '{"v":1,"id":"%s","ok":true,"result":{"arm":"hello-sh","lang":"bash","hello":"hello, %s"}}' "$id" "$name"
