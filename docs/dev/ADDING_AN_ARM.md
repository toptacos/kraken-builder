# Adding an arm

1. `cp -R arms/echo arms/weather`
2. Change `name`, `entrypoint`, `actions` in `arm.yaml`.
3. Implement `handle`.
4. Add `tests/test_weather.py` that loads from `arms/` and calls one action plus one denial.
5. `make e2e`

Do not import new cloud SDKs from `kraken.core`.
