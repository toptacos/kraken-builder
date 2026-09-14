-- Apply only when the control plane has users. Local CLI does not need this.

CREATE TABLE IF NOT EXISTS users (
    id           BIGSERIAL PRIMARY KEY,
    email        TEXT NOT NULL UNIQUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tentacle_listings (
    id           BIGSERIAL PRIMARY KEY,
    slug         TEXT NOT NULL UNIQUE,
    name         TEXT NOT NULL,
    repo_url     TEXT,
    license      TEXT NOT NULL DEFAULT 'MIT',
    featured     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS licenses (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT REFERENCES users(id),
    listing_id   BIGINT REFERENCES tentacle_listings(id),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
