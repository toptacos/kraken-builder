"""AWS Code* / Security Hub style event → taco. No AWS SDK."""


def parse(payload: dict) -> dict | None:
    detail = payload.get("detail") or payload
    user = (
        detail.get("user")
        or (detail.get("userIdentity") or {}).get("userName")
        or payload.get("user")
    )
    source = payload.get("source") or ""
    if "securityhub" in source or detail.get("type") == "Security Hub Findings - Imported":
        if (detail.get("findings") or [{}])[0].get("Workflow", {}).get("Status") == "RESOLVED" or detail.get("resolved"):
            return {"user": user or "aws", "kind": "security", "note": "aws:securityhub"}
    if "codepipeline" in source and detail.get("state") == "SUCCEEDED":
        return {"user": user or "aws", "kind": "custom", "tacos": 2, "note": "aws:codepipeline"}
    return None
