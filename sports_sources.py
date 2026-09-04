from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from models import Event, SourceRecord
from source_registry import source_by_key


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha1(value.encode('utf-8')).hexdigest()[:20]}"


def _event(*, source_key: str, external_id: str, title: str, start_date: str,
           start_time: str | None, venue: str, city: str, url: str | None,
           tags: list[str], quality_note: str) -> Event:
    source = source_by_key(source_key)
    source_name = source.name if source else source_key
    return Event(
        id=_stable_id(source_key, external_id),
        title=title,
        event_type="Sport",
        category="Sport",
        start_date=start_date,
        end_date=None,
        start_time=start_time,
        venue=venue,
        city=city,
        region="Örebro län" if city == "Örebro" else "",
        country="Sverige",
        official_url=url,
        ticket_url=None,
        status="confirmed",
        source_names=[source_name],
        source_count=1,
        source_records=[SourceRecord(
            source=source_name,
            external_id=external_id,
            source_url=url or (source.url if source else None),
            fetched_at=_now_iso(),
            raw_title=title,
        )],
        verified_at=_now_iso(),
        created_at=_now_iso(),
        updated_at=_now_iso(),
        description="",
        tags=tags,
        is_demo=False,
        data_quality="source_verified",
        quality_notes=[quality_note],
        price_status="unknown",
    )


def _clean_lines(html_text: str) -> list[str]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    return [re.sub(r"\s+", " ", x).strip() for x in soup.get_text("\n", strip=True).splitlines() if x.strip()]


def parse_osk_schedule_html(html_text: str, *, source_url: str, team_label: str) -> list[Event]:
    """Parse high-confidence ÖSK fixture blocks from the official schedule pages.

    Only home games at Behrn Arena are emitted. Away fixtures are useful team data,
    but they are not local Örebro discovery events and must not pollute the city feed.
    """
    lines = _clean_lines(html_text)
    out: list[Event] = []
    seen: set[tuple[str, str]] = set()

    for i, line in enumerate(lines):
        if line != "Datum" or i + 1 >= len(lines):
            continue
        date_text = lines[i + 1]
        mdate = re.fullmatch(r"(\d{1,2})\s+([A-Za-zÅÄÖåäö]+)\s+(20\d{2})", date_text)
        if not mdate:
            continue
        months = {
            "januari": 1, "februari": 2, "mars": 3, "april": 4, "maj": 5, "juni": 6,
            "juli": 7, "augusti": 8, "september": 9, "oktober": 10, "november": 11, "december": 12,
        }
        month = months.get(mdate.group(2).lower())
        if not month:
            continue
        start_date = f"{int(mdate.group(3)):04d}-{month:02d}-{int(mdate.group(1)):02d}"

        # Expect Avspark and Plats shortly after Datum.
        nearby = lines[i + 2:i + 10]
        try:
            kick_idx = nearby.index("Avspark")
            start_time = nearby[kick_idx + 1] if re.fullmatch(r"\d{1,2}:\d{2}", nearby[kick_idx + 1]) else None
        except (ValueError, IndexError):
            start_time = None
        try:
            place_idx = nearby.index("Plats")
            venue = nearby[place_idx + 1]
        except (ValueError, IndexError):
            continue
        if "behrn arena" not in venue.lower():
            continue

        # Locate nearest preceding 'vs' and take the adjacent team labels.
        before = lines[max(0, i - 18):i]
        vs_positions = [j for j, x in enumerate(before) if x.lower() == "vs"]
        if not vs_positions:
            continue
        j = vs_positions[-1]
        if j == 0 or j + 1 >= len(before):
            continue
        home = before[j - 1]
        away = before[j + 1]
        # Skip presentation noise around image alt text / headings.
        if home.startswith("Image") or away.startswith("Image"):
            candidates_left = [x for x in reversed(before[:j]) if not x.startswith("Image") and x not in {"Köp biljett"}]
            candidates_right = [x for x in before[j + 1:] if not x.startswith("Image") and x not in {"Köp biljett", "Herrlaget", "Damlaget", "Superettan", "Elitettan"}]
            if candidates_left:
                home = candidates_left[0]
            if candidates_right:
                away = candidates_right[0]

        if "örebro sk" not in home.lower():
            # Venue is an extra safeguard, but the official schedule can contain matches
            # at Behrn Arena where ÖSK is nominally away (e.g. derby). Only own home rows.
            continue

        title = f"{home} – {away}"
        key = (title.lower(), start_date)
        if key in seen:
            continue
        seen.add(key)
        ext = f"{team_label}|{home}|{away}|{start_date}|{start_time or ''}|{venue}"
        out.append(_event(
            source_key="osk_fotboll",
            external_id=ext,
            title=title,
            start_date=start_date,
            start_time=start_time,
            venue=venue,
            city="Örebro",
            url=source_url,
            tags=["Sport", "Fotboll", team_label],
            quality_note="Match importerad från ÖSK Fotbolls officiella spelschema; endast hemmamatcher i Örebro tas med",
        ))
    return out


def osk_events() -> list[Event]:
    source = source_by_key("osk_fotboll")
    urls = [
        ("https://oskfotboll.se/ga-pa-match/spelschema-herr/2026", "ÖSK Herr"),
        ("https://oskfotboll.se/ga-pa-match/spelschema-dam/2026", "ÖSK Dam"),
    ]
    events: list[Event] = []
    for url, label in urls:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Upplevio/0.20 (+event discovery prototype)"})
        r.raise_for_status()
        events.extend(parse_osk_schedule_html(r.text, source_url=url, team_label=label))
    return events


_MONTHS = {
    "januari": 1, "februari": 2, "mars": 3, "april": 4, "maj": 5, "juni": 6,
    "juli": 7, "augusti": 8, "september": 9, "oktober": 10, "november": 11, "december": 12,
}


def parse_orebro_hockey_article_html(html_text: str, *, source_url: str) -> list[Event]:
    """Parse explicit schedule sentences from Örebro Hockey official articles.

    This is intentionally a fallback/pilot parser. It only accepts lines with a full
    Swedish date, a matchup, and a stated venue. Only games in Behrn Arena are emitted.
    """
    lines = _clean_lines(html_text)
    text = "\n".join(lines)
    out: list[Event] = []
    seen: set[tuple[str, str]] = set()

    # Article format: 'Torsdag 24 september ... Örebro vs Björklöven' and nearby
    # 'Nedsläpp kl 18:00' / 'Matchen spelas i Behrn Arena', or equivalent prose.
    date_re = re.compile(r"(?:måndag|tisdag|onsdag|torsdag|fredag|lördag|söndag)\s+(\d{1,2})\s+([a-zåäö]+)(?:\s+(20\d{2}))?", re.I)
    for m in date_re.finditer(text):
        day = int(m.group(1)); month = _MONTHS.get(m.group(2).lower())
        if not month:
            continue
        year = int(m.group(3) or 2026)
        start_date = f"{year:04d}-{month:02d}-{day:02d}"
        chunk = text[m.start():m.start() + 500]
        if "behrn arena" not in chunk.lower():
            continue
        matchup = re.search(r"([A-ZÅÄÖ][^\n,.]{1,80}?)\s+(?:vs|–|-)\s+([^\n,.]{2,80})", chunk, re.I)
        if not matchup:
            continue
        home = re.sub(r"\s+", " ", matchup.group(1)).strip(" .")
        away = re.sub(r"\s+", " ", matchup.group(2)).strip(" .")
        home = re.sub(r"^(?:måndag|tisdag|onsdag|torsdag|fredag|lördag|söndag)\s+\d{1,2}\s+[a-zåäö]+(?:\s+20\d{2})?\s+", "", home, flags=re.I).strip()
        if "örebro" not in home.lower():
            continue
        tm = re.search(r"(?:nedsläpp(?:\s+kl)?|kl)\s*(\d{1,2}:\d{2})", chunk, re.I)
        start_time = tm.group(1) if tm else None
        title = f"{home} – {away}"
        key = (title.lower(), start_date)
        if key in seen:
            continue
        seen.add(key)
        out.append(_event(
            source_key="orebro_hockey",
            external_id=f"{title}|{start_date}|{start_time or ''}|Behrn Arena",
            title=title,
            start_date=start_date,
            start_time=start_time,
            venue="Behrn Arena",
            city="Örebro",
            url=source_url,
            tags=["Sport", "Hockey", "SHL"],
            quality_note="Match importerad från Örebro Hockeys officiella publicerade spelschema; pilotkälla",
        ))
    return out


def orebro_hockey_events() -> list[Event]:
    # Stable official season-schedule article. Prefer a proper calendar/feed later
    # if a documented machine-readable endpoint becomes available.
    url = "https://www.orebrohockey.se/article/yfqatew-3afc1/view"
    r = requests.get(url, timeout=20, headers={"User-Agent": "Upplevio/0.20 (+event discovery prototype)"})
    r.raise_for_status()
    return parse_orebro_hockey_article_html(r.text, source_url=url)
