# Put this tree on kraken.topta.co

The marketing site is static (`website/`). The CLI is this repo. api.topta.co is the existing Laravel app — copy `control-plane/laravel-api/` into it.

## Laptop

```
unzip kraken-builder-archive.zip
cd kraken-builder
export PYTHONPATH="$PWD"
python3 -m kraken init
python3 -m kraken vanilla
python3 -m http.server 8080 --directory website
```

## Site

Rsync the `website/` folder to the host that already serves other topta.co SPAs:

```
rsync -av --delete website/ user@host:/var/www/kraken.topta.co/
```

Point the vhost at that directory. OG image: `img/kit-2026/og-1200x630.jpg`.

## API

```
# on api.topta.co
cp control-plane/laravel-api/routes/kraken.php routes/
cp control-plane/laravel-api/migrations/* database/migrations/
php artisan migrate
```

Do not enable Stripe live. Session routes are stubs until you add auth middleware.

## Training media

`website/media/train-*.mp4` plus `website/courses.html`.
