# Install

TopTaco product site: https://kraken.topta.co  
API: https://api.topta.co

```bash
# after Kraken is on PATH
kraken tentacle add ./kraken-tentacle-taco
python3 bin/kraken taco after_install
# or interactive
python3 bin/kraken taco init
```

This tree is the tentacle. Core Kraken applies `hooks.after_install`. The `bin/kraken` file here is a shim if core is not installed.

Docker smoke:

```bash
docker build -t taco .
docker run --rm taco
```
