# Kraken CLI

**One binary. Many tentacles.** Local-first CLI plugin runner. Not the [crypto exchange](https://www.kraken.com).

JSON in → policy → exec → JSON out. MIT core. Premium is fleet + portal, not a fatter CLI.

```
curl -fsSL https://kraken.topta.co/install.sh | sh
kraken demo
```

That install puts `kraken` and `k` on PATH, installs vanilla tentacles, and prints one geo lookup JSON. First success in under 60s.

```
kraken doctor
kraken run filesort scan --payload '{"path":"."}'
kraken grant expose
kraken run expose plan --payload '{"host":"panel.kraken.localhost"}'
```

## Public input

| Channel | Use |
|---------|-----|
| [Discussions · install](https://github.com/toptacos/kraken-builder/discussions) | Install, PATH, python wrapper |
| [Discussions · tentacle](https://github.com/toptacos/kraken-builder/discussions) | Write an arm. Paste tentacle.yaml, no keys |
| [Discussions · showcase](https://github.com/toptacos/kraken-builder/discussions) | Homelab / Pi / consultant jobs |
| [Issues](https://github.com/toptacos/kraken-builder/issues) | Bugs with a repro. Never paste `~/.kraken/keys` |
| [Register](https://kraken.topta.co/register) | List a tentacle for catalog review |

Template: [`examples/tentacles/_template/`](examples/tentacles/_template/). Contract: JSON on stdin, JSON on stdout. Core never imports your source.

## Links

Site: https://kraken.topta.co  
Install: https://kraken.topta.co/cli  
Use cases: https://kraken.topta.co/use-cases  
Changelog: https://kraken.topta.co/changelog  
Pricing: https://kraken.topta.co/pricing (Starter $19 / Pro $49 / Enterprise $149 — checkout on profile.topta.co)  
API: https://api.topta.co

Repos: [kraken-builder](https://github.com/toptacos/kraken-builder) · [tentacles](https://github.com/toptacos/kraken-tentacles) · [suckers](https://github.com/toptacos/kraken-suckers)

Homebrew (fill sha256 after tagging v0.1.1):

```
brew install toptacos/kraken/kraken-cli
```

Topics: `cli` · `homelab` · `raspberry-pi` · `plugins` · `local-first` · `self-hosted`

A TopTaco product on topta.co. Brand: tentacle-K, ink `#0B1220`, teal `#2FD0C6`, foam `#E7F6F6`, gold `#e7c56a`.
