# Stores

`~/.kraken/config.yaml` and project `.kraken/config.yaml` merge.

```yaml
stores:
  - name: local
    uri: local://data
  - name: usb
    uri: file:///media/backup/kraken
    optional: true
```

`store` tentacle writes packs. `vault` wraps secrets. Multiple URIs are destinations, not a mesh. S3 in this tree is a folder mirror unless you add IAM later.
