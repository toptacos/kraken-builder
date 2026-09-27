# Hello-world tentacles

Same contract in every language: JSON in on stdin, JSON out on stdout, exit 0.

```bash
# scripts
kraken tentacle add examples/tentacles/hello-world/python
kraken run hello-py ping

# compiled
./examples/tentacles/hello-world/build.sh
kraken tentacle add examples/tentacles/hello-world/c
kraken run hello-c ping
```

| Dir | Language | Run as | Build |
|---|---|---|---|
| `python/` | Python 3 | `python3 handler.py` | none |
| `bash/` | Bash | `bash handler.sh` | none |
| `js/` | Node | `node handler.js` | none |
| `php/` | PHP | `php handler.php` | none |
| `ruby/` | Ruby | `ruby handler.rb` | none |
| `perl/` | Perl | `perl handler.pl` | none |
| `go/` | Go | `go run handler.go` | `go build -o hello` |
| `rust/` | Rust | compiled `hello` | `rustc -O -o hello handler.rs` |
| `c/` | C | compiled `hello` | `gcc -O2 -o hello handler.c` |
| `cpp/` | C++ | compiled `hello` | `g++ -O2 -o hello handler.cpp` |
| `java/` | Java | `java -cp . Hello` via `run.sh` | `javac Hello.java` |

Core maps suffixes in `kraken.core.contract._argv`. Compiled files with no suffix are executed as-is.

Payload: `{ "name": "world" }` → `result.hello` is `"hello, world"`.
