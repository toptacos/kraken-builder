"""Inbound adapters. Vendors push; taco does not pull."""
from . import aws, gchat, github, gitlab, google, slack, teams

ROUTES = {
    "github": github.parse,
    "gitlab": gitlab.parse,
    "gchat": gchat.parse,
    "googlechat": gchat.parse,
    "slack": slack.parse,
    "teams": teams.parse,
    "msteams": teams.parse,
    "aws": aws.parse,
    "amazon": aws.parse,
    "google": google.parse,
}


def parse(channel: str, payload: dict) -> dict | None:
    fn = ROUTES.get((channel or "").lower())
    if not fn:
        return None
    return fn(payload)
