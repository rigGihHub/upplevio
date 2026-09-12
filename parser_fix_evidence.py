"""Evidence-only diagnostics for detail gaps.

Fetch/analyse is intentionally separate from enrichment: this module never mutates Event.
It classifies whether a selected page contains explicit evidence for the missing field.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from booking_enrichment import extract_detail_facts
from showtime_enrichment import extract_explicit_showtime


def _safe_public_http_url(url: str) -> bool:
    try:
        p = urlparse(str(url or '').strip())
        if p.scheme not in {'http', 'https'} or not p.hostname:
            return False
        host = p.hostname.lower()
        if host in {'localhost'} or host.endswith('.local'):
            return False
        try:
            infos = socket.getaddrinfo(host, p.port or (443 if p.scheme == 'https' else 80), type=socket.SOCK_STREAM)
        except socket.gaierror:
            # Keep diagnostics testable/offline; DNS is rechecked by requests at fetch time.
            return True
        for info in infos:
            addr = ipaddress.ip_address(info[4][0])
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast:
                return False
        return True
    except Exception:
        return False


def _page_text(html_text: str) -> str:
    soup = BeautifulSoup(html_text or '', 'html.parser')
    for node in soup(['script', 'style', 'noscript']):
        node.decompose()
    return re.sub(r'\s+', ' ', soup.get_text(' ', strip=True)).strip()


def _snippet(text: str, pattern: str, *, radius: int = 100) -> str:
    m = re.search(pattern, text, re.I)
    if not m:
        return ''
    start = max(0, m.start() - radius); end = min(len(text), m.end() + radius)
    return text[start:end].strip()


def analyze_gap_evidence(html_text: str, *, field: str, current_start_time: str | None = None):
    """Return evidence classification without changing imported event data."""
    text = _page_text(html_text)
    if not text:
        return {'status':'Ingen evidens', 'kind':'empty_page', 'snippet':'', 'value':None,
                'explanation':'Sidan gav ingen användbar text.'}

    if field in {'start_time','end_time'}:
        hit = extract_explicit_showtime(html_text, current_start_time=current_start_time)
        key = 'start_time' if field == 'start_time' else 'end_time'
        if hit and hit.get(key):
            val = hit[key]
            snip = _snippet(text, rf'\b{re.escape(val.replace(":", "."))}\b|\b{re.escape(val)}\b')
            return {'status':'Parserkandidat', 'kind':hit.get('evidence','explicit_time'), 'snippet':snip,
                    'value':val, 'explanation':'Sidan innehåller en uttrycklig tid som den konservativa evidensparsern kan identifiera.'}
        # We deliberately distinguish duration-only text from exact end evidence.
        dur = _snippet(text, r'\b(?:ca\.?\s*)?\d{1,3}\s*(?:minuter|min)\b|\blängd\b')
        if field == 'end_time' and dur:
            return {'status':'Källan saknar exakt värde', 'kind':'duration_only', 'snippet':dur, 'value':None,
                    'explanation':'Sidan beskriver längd men ingen verifierad exakt sluttid. Upplevio ska inte räkna fram en sluttid.'}

    facts = extract_detail_facts(html_text)
    fact_map = {'door_time':'door_time','age_limit':'age_limit','price':'price','precise_venue':'venue'}
    if field in fact_map and facts.get(fact_map[field]) is not None:
        val = facts[fact_map[field]]
        patterns = {
            'door_time': r'\b(?:insläpp|dörr(?:ar|arna)?|foaj[eé])\b[^.]{0,80}\b\d{1,2}[:.]\d{2}\b',
            'age_limit': r'\b(?:åldersgräns|från)\b[^.]{0,80}\b\d{1,2}\s*år\b',
            'price': r'\b(?:biljettpris|entr[eé]pris|pris)\b[^.]{0,80}\b\d{1,5}(?:[.,]00)?\s*(?:kr|kronor)\b',
            'precise_venue': re.escape(str(val)),
        }
        return {'status':'Parserkandidat', 'kind':'explicit_detail', 'snippet':_snippet(text, patterns[field]),
                'value':val, 'explanation':'Sidan innehåller uttryckligt märkt praktisk information som evidensparsern kan identifiera.'}

    if field == 'booking':
        # Booking is intentionally not auto-diagnosed here: link safety/enrichment has separate logic.
        return {'status':'Ej analyserad här', 'kind':'booking_separate', 'snippet':'', 'value':None,
                'explanation':'Bokningslänkar har en separat säkerhets- och partneranalys och klassas inte av denna evidensvy.'}

    labels = {
        'door_time': r'\b(?:insläpp|dörr(?:ar|arna)?|foaj[eé])\b',
        'age_limit': r'\b(?:åldersgräns|\d{1,2}\s*år)\b',
        'price': r'\b(?:biljettpris|entr[eé]pris|pris)\b',
        'precise_venue': r'\b(?:plats|lokal|arena|kongress|teater|salong)\b',
    }
    hint = _snippet(text, labels.get(field, r'$a'))
    if hint:
        return {'status':'Manuell granskning', 'kind':'weak_context', 'snippet':hint, 'value':None,
                'explanation':'Relevant kontext finns på sidan, men inget värde uppfyller Upplevios konservativa parserregler.'}
    return {'status':'Källan verkar sakna uppgiften', 'kind':'not_found', 'snippet':'', 'value':None,
            'explanation':'Ingen uttrycklig evidens för det valda fältet hittades i sidtexten.'}


def fetch_gap_evidence(url: str, *, field: str, current_start_time: str | None = None, timeout: int = 10):
    if not _safe_public_http_url(url):
        return {'status':'Kunde inte granska', 'kind':'unsafe_url', 'snippet':'', 'value':None,
                'explanation':'URL:en är inte en tillåten publik HTTP/HTTPS-adress.', 'http_status':None}
    try:
        r = requests.get(url, timeout=timeout, headers={'User-Agent':'Upplevio/0.71 (+parser evidence diagnostic)'}, allow_redirects=True)
        r.raise_for_status()
    except Exception as exc:
        return {'status':'Kunde inte granska', 'kind':'fetch_error', 'snippet':'', 'value':None,
                'explanation':f'Sidan kunde inte hämtas: {type(exc).__name__}.', 'http_status':getattr(getattr(exc,'response',None),'status_code',None)}
    result = analyze_gap_evidence(r.text, field=field, current_start_time=current_start_time)
    result['http_status'] = r.status_code
    result['final_url'] = getattr(r, 'url', url)
    return result
