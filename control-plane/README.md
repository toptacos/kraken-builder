# Control plane (kraken.topta.co)

Target stack: Laravel or Symfony + FrankenPHP + Postgres.

This slice is a **skeleton**, not a full Laravel install (Composer is not available in the authoring environment).

```
control-plane/
  README.md
  public/index.php     # health + catalog JSON
  config/app.php
  database/schema.sql  # Postgres when accounts exist
```

Local smoke (no Postgres required):

```bash
php -S 127.0.0.1:8081 -t control-plane/public
curl http://127.0.0.1:8081/health
```

When Composer exists:

```bash
composer create-project laravel/laravel control-plane-app
# mount this catalog + auth; use frankenphp php-cli / frankenphp run
```

Do not require the control plane for `kraken run` on a device.
