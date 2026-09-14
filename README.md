# Kraken CLI

**One binary. Many tentacles.** Local-first CLI plugin runner. 

JSON in → policy → exec → JSON out. **MIT open source.** Optional billing lives in `kraken.billing` and is not required to run.

![Kraken tentacle-K](https://kraken.topta.co/og-1200x630.jpg)

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
Optional seats (after you have a tentacle): https://kraken.topta.co/pricing — docs/BILLING.md  
API: https://api.topta.co

Repos: [kraken-builder](https://github.com/toptacos/kraken-builder) · [tentacles](https://github.com/toptacos/kraken-tentacles) · [suckers](https://github.com/toptacos/kraken-suckers)

Homebrew:

```
brew install toptacos/kraken/kraken-cli
```

Optional billing extra (same tree, not required):

```
pip install 'kraken-cli[billing]'
```

Topics: `cli` · `homelab` · `raspberry-pi` · `plugins` · `local-first` · `self-hosted`

A TopTaco product on topta.co. Brand: tentacle-K, ink `#0B1220`, teal `#2FD0C6`, foam `#E7F6F6`, gold `#e7c56a`.
