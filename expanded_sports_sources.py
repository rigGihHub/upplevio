"""Public bandy tickets and explicitly advertised badminton fixtures in Örebro."""
from datetime import date, datetime
import json
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from sports_sources import _event

BANDY_URL = "https://orebroskbandy.ticketco.events/se/sv"
BADMINTON_URL = "https://www.orebrobadminton.com/"


def parse_bandy_html(html):
    soup = BeautifulSoup(html, "html.parser")
    # TicketCo's visible local clock is authoritative; its JSON-LD uses Z even
    # when the displayed clock is Swedish local time. Only take the end date.
    end_dates = {}
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            raw = json.loads(script.string or script.get_text())
            if isinstance(raw, dict) and raw.get("@type") == "Event":
                end_dates[(raw.get("url") or "").rsplit("/", 1)[-1]] = (raw.get("endDate") or "")[:10]
        except (ValueError, TypeError):
            continue
    events, seen = [], set()
    for card in soup.select(".tc-events-list--item"):
        link, place = card.select_one("a.tc-events-list--title[href]"), card.select_one(".tc-events-list--place-time")
        if not link or not place:
            continue
        title, url = link.get_text(" ", strip=True), urljoin(BANDY_URL, link["href"])
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "orebroskbandy.ticketco.events" or "/e/" not in parsed.path:
            continue
        if re.search(r"säsongs(?:kort|biljett)", title, re.I):
            continue
        match = re.fullmatch(r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s*@\s*(.+)", place.get_text(" ", strip=True))
        if not match or not re.search(r"\bÖrebro\b", match[3], re.I):
            continue
        try:
            when = datetime.strptime(f"{match[1]} {match[2]}", "%d.%m.%Y %H:%M")
        except ValueError:
            continue
        key = parsed.path.rsplit("/", 1)[-1]
        identity = f"{key}:{when.date()}:{match[2]}"
        if identity in seen:
            continue
        seen.add(identity)
        event = _event(source_key="osk_bandy", external_id=identity, title=title,
            start_date=when.date().isoformat(), start_time=match[2], venue=match[3], city="Örebro",
            url=url, tags=["Sport", "Bandy"], quality_note="ÖSK Bandys offentliga biljettkalender · lokalt visad starttid")
        event.ticket_url = url
        try:
            end = date.fromisoformat(end_dates.get(key, ""))
            if end >= when.date():
                event.end_date = end.isoformat()
        except ValueError:
            pass
        # Only extract the explicitly labelled ticket amount, never youth free
        # admission or an unrelated number in the match name.
        prices = re.findall(r"Biljett till (?:en dag|båda dagarna)\s+(\d+)\s+kronor", card.get_text(" ", strip=True), re.I)
        if prices:
            event.price_min, event.price_max = min(map(int, prices)), max(map(int, prices))
            event.price_status = "known"
        events.append(event)
    return events


def bandy_events():
    response = requests.get(BANDY_URL, timeout=20)
    response.raise_for_status()
    return parse_bandy_html(response.text)


def parse_badminton_article(html, source_url):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one(".sa-news-detail .sa-paragraph")
    if article is None:
        return []
    published = article.select_one(".sa-paragraph__date")
    body = article.select_one(".sa-paragraph__body")
    preamble = article.select_one(".sa-paragraph__preamble")
    if not published or not body or not preamble:
        return []
    text = preamble.get_text(" ", strip=True) + " " + body.get_text(" ", strip=True)
    if not re.search(r"kom och (?:heja|stötta)", text, re.I) or not re.search(r"\bBackahallen\b", text, re.I):
        return []
    months = {"januari": 1, "februari": 2, "mars": 3, "april": 4, "maj": 5, "juni": 6,
              "juli": 7, "augusti": 8, "september": 9, "oktober": 10, "november": 11, "december": 12}
    match = re.search(r"\b(\d{1,2})\s+(" + "|".join(months) + r")\b(?:\s+(20\d{2}))?", preamble.get_text(" ", strip=True), re.I)
    if not match:
        return []
    try:
        publication = date.fromisoformat(published.get_text(strip=True)[:10])
        year = int(match[3]) if match[3] else publication.year
        day = date(year, months[match[2].lower()], int(match[1]))
        # Without an explicit year, only accept a nearby date in the publication
        # year. Older stories and New Year ambiguity require better source data.
        if not match[3] and not -7 <= (day - publication).days <= 120:
            return []
    except ValueError:
        return []
    result, seen = [], set()
    for line in body.get_text("\n", strip=True).splitlines():
        fixture = re.fullmatch(r"(\d{1,2})[.:](\d{2}):\s*([^()]+?)\s*[-–]\s*([^()]+?)(?:\s*\(Bana[^)]*\))?", line.strip(), re.I)
        if not fixture or int(fixture[1]) > 23 or int(fixture[2]) > 59:
            continue
        clock = f"{int(fixture[1]):02d}:{fixture[2]}"
        title = f"Badminton: {fixture[3].strip()} – {fixture[4].strip()}"
        identity = f"{source_url}:{day}:{clock}:{title}"
        if identity in seen:
            continue
        seen.add(identity)
        result.append(_event(source_key="orebro_badminton", external_id=identity, title=title,
            start_date=day.isoformat(), start_time=clock, venue="Backahallen", city="Örebro", url=source_url,
            tags=["Sport", "Badminton"], quality_note="Officiell publik matchinbjudan · datum och speltid ur artikeltexten"))
    return result


def badminton_events():
    response = requests.get(BADMINTON_URL, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    result, seen = [], set()
    for article in soup.select(".sa-news-feed__item"):
        text = article.get_text(" ", strip=True)
        link = article.select_one(".sa-news-feed__title a[href]")
        if not link or not re.search(r"kom och (?:heja|stötta)", text, re.I):
            continue
        url = urljoin(BADMINTON_URL, link["href"])
        parsed = urlparse(url)
        if parsed.netloc != "www.orebrobadminton.com" or parsed.path != "/nyheter/" or url in seen:
            continue
        if len(seen) >= 4:
            break
        seen.add(url)
        detail = requests.get(url, timeout=20)
        detail.raise_for_status()
        result.extend(parse_badminton_article(detail.text, url))
    return result
