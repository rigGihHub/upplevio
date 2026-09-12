import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlencode, urlparse

from booking_partners import attribution_for_url
from conversion_attribution import create_or_get_outbound_click

DEFAULT_TTL_SECONDS = 1800

@dataclass(frozen=True)
class RedirectResult:
    click_id: str
    destination_url: str
    event_id: str
    partner_key: str
    partner_name: str
    campaign_id: str | None


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _safe_destination(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.scheme == "https" and bool(parsed.hostname)


def make_redirect_token(*, event, destination_url: str, secret: str, now: int | None = None) -> str:
    if not secret or len(secret) < 32:
        raise ValueError("Redirect secret must be at least 32 characters")
    if not _safe_destination(destination_url):
        raise ValueError("Only absolute HTTPS destinations are allowed")
    attribution = attribution_for_url(destination_url)
    payload = {
        "v": 1,
        "jti": secrets.token_hex(16),
        "iat": int(now if now is not None else time.time()),
        "event_id": str(event.id),
        "partner_key": attribution["key"],
        "partner_name": attribution["name"],
        "campaign_id": getattr(event, "sponsor_campaign_id", None),
        "source": ", ".join(getattr(event, "source_names", []) or []) or "Okänd källa",
        "event_type": getattr(event, "event_type", None) or "Okänd typ",
        "destination_url": destination_url,
    }
    body = _b64e(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    sig = _b64e(hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())
    return body + "." + sig


def verify_redirect_token(token: str, *, secret: str, now: int | None = None, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> dict:
    if not secret or len(secret) < 32:
        raise ValueError("Redirect tracking is not configured")
    try:
        body, supplied_sig = token.split(".", 1)
        expected_sig = _b64e(hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied_sig, expected_sig):
            raise ValueError("Invalid redirect signature")
        payload = json.loads(_b64d(body).decode("utf-8"))
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Malformed redirect token") from exc
    if payload.get("v") != 1 or not payload.get("jti") or not payload.get("event_id"):
        raise ValueError("Incomplete redirect token")
    issued = int(payload.get("iat", 0))
    current = int(now if now is not None else time.time())
    if issued > current + 60:
        raise ValueError("Redirect token issued in the future")
    if current - issued > ttl_seconds:
        raise ValueError("Redirect token expired")
    if not _safe_destination(payload.get("destination_url", "")):
        raise ValueError("Unsafe redirect destination")
    return payload


def build_tracked_url(*, event, destination_url: str, public_base_url: str | None, secret: str | None) -> str:
    if not public_base_url or not secret or len(secret) < 32:
        return destination_url
    parsed = urlparse(public_base_url)
    if parsed.scheme != "https" or not parsed.hostname:
        return destination_url
    token = make_redirect_token(event=event, destination_url=destination_url, secret=secret)
    base = public_base_url.split("?", 1)[0].rstrip("/") + "/"
    return base + "?" + urlencode({"go": token})


def process_redirect(token: str, *, secret: str, db_path=None, now: int | None = None) -> RedirectResult:
    payload = verify_redirect_token(token, secret=secret, now=now)
    click_id = "upc_" + payload["jti"]
    click = create_or_get_outbound_click(
        click_id=click_id,
        event_id=payload["event_id"],
        partner_key=payload["partner_key"],
        partner_name=payload["partner_name"],
        destination_url=payload["destination_url"],
        campaign_id=payload.get("campaign_id"),
        context={"redirect_version": 1, "source": payload.get("source"), "event_type": payload.get("event_type"), "partner": payload.get("partner_name")},
        db_path=db_path,
    )
    return RedirectResult(
        click_id=click.click_id,
        destination_url=payload["destination_url"],
        event_id=payload["event_id"],
        partner_key=payload["partner_key"],
        partner_name=payload["partner_name"],
        campaign_id=payload.get("campaign_id"),
    )
