import re
from bs4 import BeautifulSoup

_BLOCKED_CONTEXT = (
    "öppettid", "biljettkassa", "telefon", "telefontid", "kundservice", "reception",
)
_STRONG_CONTEXT = (
    "pågår", "tider", "tid:", "tid ", "slut", "föreställning", "evenemang",
)


def _clock(hour: str, minute: str) -> str | None:
    try:
        h = int(hour); m = int(minute)
    except (TypeError, ValueError):
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return f"{h:02d}:{m:02d}"


def _clean_text(html_text: str) -> str:
    soup = BeautifulSoup(html_text or "", "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def _nearby(text: str, start: int, end: int, radius: int = 90) -> str:
    return text[max(0, start-radius): min(len(text), end+radius)].lower()


def extract_explicit_showtime(html_text: str, *, current_start_time: str | None = None):
    """Extract only explicit event clock ranges/end markers from an event detail page.

    The function never derives an end time from duration text such as "ca 60 minuter".
    If an existing start time is known, a range matching that start time is considered
    strong evidence even without nearby labels. Otherwise the range needs event-time
    context and must not sit in obvious opening-hours/contact context.
    """
    text = _clean_text(html_text)
    if not text:
        return None

    current = (current_start_time or "").strip()[:5] or None
    candidates = []
    # Explicit intervals: 10.00–16.00 / 18:00 - 23:00 / kl. 18:00–23:00
    for m in re.finditer(r"(?<!\d)(\d{1,2})[:.](\d{2})\s*[–—-]\s*(\d{1,2})[:.](\d{2})(?!\d)", text):
        start = _clock(m.group(1), m.group(2)); end = _clock(m.group(3), m.group(4))
        if not start or not end:
            continue
        context = _nearby(text, m.start(), m.end())
        blocked = any(term in context for term in _BLOCKED_CONTEXT)
        strong = any(term in context for term in _STRONG_CONTEXT)
        matches_existing = bool(current and start == current)
        if blocked and not matches_existing:
            continue
        if not matches_existing and not strong:
            continue
        candidates.append((0 if matches_existing else 1, m.start(), start, end, "explicit_range"))

    # Some event pages publish a separate exact start marker, e.g. "20:00 – start".
    # This is accepted only with an explicit start label and outside blocked service contexts.
    for m in re.finditer(r"(?<!\d)(\d{1,2})[:.](\d{2})\s*[–—-]\s*start\b", text, re.I):
        start = _clock(m.group(1), m.group(2))
        if not start:
            continue
        context = _nearby(text, m.start(), m.end())
        if any(term in context for term in _BLOCKED_CONTEXT):
            continue
        # When an already verified start exists, only matching evidence is useful.
        if current and start != current:
            continue
        candidates.append((0, m.start(), start, None, "explicit_start_marker"))

    # Some event pages publish a separate exact end marker, e.g. "23:00 – Slut".
    # This is useful only when the event already has a verified start time.
    if current:
        for m in re.finditer(r"(?<!\d)(\d{1,2})[:.](\d{2})\s*[–—-]\s*slut\b", text, re.I):
            end = _clock(m.group(1), m.group(2))
            if not end:
                continue
            context = _nearby(text, m.start(), m.end())
            if any(term in context for term in _BLOCKED_CONTEXT):
                continue
            candidates.append((0, m.start(), current, end, "explicit_end_marker"))

    if not candidates:
        return None
    candidates.sort(key=lambda row: (row[0], row[1]))
    _, _, start, end, evidence = candidates[0]
    return {"start_time": start, "end_time": end, "evidence": evidence}
