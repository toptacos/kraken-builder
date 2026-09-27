# Cross compile

board ships as `handler.sh` + `handler.py`, the same runtime as official `jev-ai`. There is no Go matrix and no `dist/` binaries.

CI runs the Python suite on ubuntu, macos, and windows. That is the portability story.
