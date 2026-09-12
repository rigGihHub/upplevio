from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import re
import requests
from bs4 import BeautifulSoup
from booking_partners import attribution_for_url, identify_booking_partner
from showtime_enrichment import extract_explicit_showtime

# Strong CTAs may be used on the official event host or on a known ticket partner.
STRONG_CTA_TERMS = (
    ("köp din biljett", "ticket"),
    ("köp biljetter", "ticket"),
    ("köp biljett", "ticket"),
    ("boka nu", "booking"),
    ("boka", "booking"),
)

# A generic "Biljetter" label is intentionally weaker: it is only accepted when
# the target itself gives strong support (known ticket partner or ticket-like path).
MEDIUM_CTA_TERMS = (("biljetter", "ticket"),)

BLOCKED_HOST_SUFFIXES = (
    "facebook.com", "instagram.com", "linkedin.com", "tiktok.com",
    "youtube.com", "youtu.be", "x.com", "twitter.com", "threads.net",
)

TICKET_PATH_HINTS = (
    "/ticket", "/tickets", "/biljett", "/biljetter", "/boka", "/booking",
    "/checkout", "/purchase", "/event/", "/events/",
)


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().strip(".")
    except Exception:
        return ""


def _same_host_or_subdomain(target_url: str, page_url: str) -> bool:
    target = _host(target_url)
    page = _host(page_url)
    if not target or not page:
        return False
    return target == page or target.endswith("." + page) or page.endswith("." + target)


def _blocked_social_host(url: str) -> bool:
    host = _host(url)
    return any(host == suffix or host.endswith("." + suffix) for suffix in BLOCKED_HOST_SUFFIXES)


def _is_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)


def _is_generic_root(url: str) -> bool:
    parsed = urlparse(url)
    path = (parsed.path or "").strip()
    return path in {"", "/"} and not parsed.query


def _ticketish_path(url: str) -> bool:
    parsed = urlparse(url)
    path = (parsed.path or "").lower()
    return any(hint in path for hint in TICKET_PATH_HINTS)


def _cta_kind(label: str):
    for term, kind in STRONG_CTA_TERMS:
        if term in label:
            return "strong", term, kind
    for term, kind in MEDIUM_CTA_TERMS:
        if term in label:
            return "medium", term, kind
    return None


def _safe_candidate(raw_href: str, page_url: str, strength: str) -> str | None:
    raw = (raw_href or "").strip()
    if not raw or raw.startswith("#"):
        return None

    # urljoin would otherwise turn e.g. javascript: or mailto: into values that
    # look link-like. Reject non-web schemes before and after joining.
    parsed_raw = urlparse(raw)
    if parsed_raw.scheme and parsed_raw.scheme.lower() not in {"http", "https"}:
        return None

    target = urljoin(page_url, raw)
    if not _is_http_url(target) or _blocked_social_host(target):
        return None

    partner = identify_booking_partner(target)
    same_host = _same_host_or_subdomain(target, page_url)

    # Unknown external hosts are never inferred to be booking providers.
    if not partner and not same_host:
        return None

    # Root homepages are not specific enough to be booking destinations.
    if _is_generic_root(target):
        return None

    # Medium CTAs need stronger target evidence than the text alone.
    if strength == "medium" and not (partner or (same_host and _ticketish_path(target))):
        return None

    return target




def _norm_time(value: str | None) -> str | None:
    if not value:
        return None
    m = re.fullmatch(r"\s*(\d{1,2})[.:](\d{2})\s*", value)
    if not m:
        return None
    hh, mm = int(m.group(1)), int(m.group(2))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return None
    return f"{hh:02d}:{mm:02d}"


def extract_detail_facts(html_text: str):
    """Extract only explicit practical facts from an official event detail page.

    No duration arithmetic, no inferred age limits and no unlabelled money values.
    """
    soup = BeautifulSoup(html_text or "", "html.parser")
    lines = [" ".join(x.split()) for x in soup.get_text("\n", strip=True).splitlines()]
    lines = [x for x in lines if x]
    joined = "\n".join(lines)
    low = joined.casefold()
    facts = {"door_time": None, "age_limit": None, "venue": None, "price": None}

    # Prefer the earliest explicitly stated public door/foyer/entry time.
    door_times = []
    patterns = [
        r"(?P<t>\d{1,2}[.:]\d{2})\s*[–-]\s*dörr(?:arna|ar)?\s+öppnar",
        r"dörr(?:arna|ar)?[^\n.]{0,70}?öppnar[^0-9\n]{0,25}(?P<t>\d{1,2}[.:]\d{2})",
        r"insläpp[^\n.]{0,70}?(?:sker\s*)?(?:kl\.?\s*)?(?P<t>\d{1,2}[.:]\d{2})",
    ]
    for pat in patterns:
        for m in re.finditer(pat, low, flags=re.I):
            t = _norm_time(m.group("t"))
            if t:
                door_times.append(t)
    if door_times:
        facts["door_time"] = min(door_times)

    # Age limit must be explicitly labelled. Preserve organizer wording.
    for i, line in enumerate(lines):
        m = re.match(r"(?i)^åldersgräns\s*[:–-]?\s*(.*)$", line)
        if not m:
            continue
        value = m.group(1).strip()
        if not value and i + 1 < len(lines):
            value = lines[i + 1].strip()
        if value and len(value) <= 140:
            facts["age_limit"] = value
        break

    # Exact venue refinement for Conventum detail pages. Only named HITTA TILL headings.
    vm = re.search(r"(?im)^HITTA TILL\s+([^\n]{3,80})$", joined)
    if vm:
        raw = " ".join(vm.group(1).split()).strip(" .:-")
        known = {
            "CONVENTUM KONGRESS": "Conventum Kongress",
            "CONVENTUM ARENA": "Conventum Arena",
            "HJALMAR BERGMAN TEATERN": "Hjalmar Bergman Teatern",
        }
        facts["venue"] = known.get(raw.upper())

    # Money is accepted only when the line itself is explicitly a ticket/entry price.
    for line in lines:
        pm = re.match(r"(?i)^(?:biljettpris|entrépris|entré|pris)\s*[:–-]?\s*(?:från\s*)?(\d{1,5})(?:[.,]00)?\s*(?:kr|kronor)\b", line)
        if pm:
            value = float(pm.group(1))
            facts["price"] = value
            break

    return facts


def extract_booking_link(html_text: str, page_url: str):
    soup = BeautifulSoup(html_text or "", "html.parser")
    candidates = []
    for a in soup.find_all("a", href=True):
        label = " ".join(a.get_text(" ", strip=True).lower().split())
        cta = _cta_kind(label)
        if not cta:
            continue
        strength, term, kind = cta
        href = _safe_candidate(a.get("href"), page_url, strength)
        if not href:
            continue
        exact = label == term
        partner = identify_booking_partner(href)
        # Prefer exact/strong labels, then known partners, then shorter labels.
        candidates.append((0 if strength == "strong" else 1,
                           0 if exact else 1,
                           0 if partner else 1,
                           len(label), href, kind, label))
    if not candidates:
        return None
    candidates.sort()
    _, _, _, _, href, kind, label = candidates[0]
    return {"url": href, "kind": kind, "label": label}


def enrich_event(event, *, timeout=10):
    if not getattr(event, "official_url", None):
        return event
    r = requests.get(event.official_url, timeout=timeout, headers={"User-Agent":"Upplevio/0.67 (+event discovery prototype)"})
    r.raise_for_status()
    showtime = extract_explicit_showtime(r.text, current_start_time=getattr(event, "start_time", None))
    if showtime:
        if not getattr(event, "start_time", None):
            event.start_time = showtime["start_time"]
        if not getattr(event, "end_time", None):
            event.end_time = showtime["end_time"]
        note = "Verifierad start-/sluttid hämtad uttryckligen från eventets detaljsida"
        if note not in event.quality_notes:
            event.quality_notes = [*event.quality_notes, note]

    facts = extract_detail_facts(r.text)
    detail_added = False
    if facts.get("door_time") and not getattr(event, "door_time", None):
        event.door_time = facts["door_time"]
        detail_added = True
    if facts.get("age_limit") and not getattr(event, "age_limit", None):
        event.age_limit = facts["age_limit"]
        detail_added = True
    if facts.get("venue") and (not getattr(event, "venue", None) or event.venue.strip().casefold() == "conventum"):
        event.venue = facts["venue"]
        detail_added = True
    if facts.get("price") is not None and getattr(event, "price_status", "unknown") == "unknown":
        event.price_min = facts["price"]
        event.price_max = facts["price"]
        event.currency = "SEK"
        event.price_status = "free" if facts["price"] <= 0 else "known"
        detail_added = True
    if detail_added:
        note = "Verifierad praktisk eventinfo hämtad uttryckligen från eventets detaljsida"
        if note not in event.quality_notes:
            event.quality_notes = [*event.quality_notes, note]

    hit = None if getattr(event, "booking_url", None) else extract_booking_link(r.text, event.official_url)
    if hit:
        event.booking_url = hit["url"]
        event.ticket_url = event.ticket_url or hit["url"]
        attribution = attribution_for_url(hit["url"])
        event.booking_partner_key = attribution["key"]
        event.booking_partner = attribution["name"]
        event.booking_partner_domain = attribution["domain"]
        event.affiliate_status = attribution["affiliate_status"]
        event.quality_notes = [*event.quality_notes, "Direkt boknings-/biljettlänk verifierad från eventets detaljsida"]
    return event


def enrich_events(events, *, max_fetches=12, workers=6, timeout=10):
    candidates = [e for e in events if getattr(e,"official_url",None)][:max_fetches]
    if not candidates:
        return events
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures={ex.submit(enrich_event,e,timeout=timeout):e for e in candidates}
        for f in as_completed(futures):
            try:
                f.result()
            except Exception:
                pass
    return events
