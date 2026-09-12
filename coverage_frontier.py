from collections import Counter, defaultdict
from datetime import date, timedelta

SEGMENTS = {
    "Stora konserter": ["konsert", "arena", "festival"],
    "Lokal livemusik": ["live", "livemusik", "jazz", "rock", "pop", "musik"],
    "Teater & scenkonst": ["teater", "scenkonst", "föreställning", "dans", "musikal"],
    "Stand-up & humor": ["stand-up", "standup", "komedi", "humor"],
    "Museum & utställning": ["museum", "utställning", "konst", "vernissage", "openart"],
    "Familj & barn": ["familj", "barn", "lov", "kids"],
    "Publiksport": ["fotboll", "hockey", "innebandy", "match", "sport"],
    "Marknad & mässa": ["marknad", "mässa", "loppis", "expo"],
    "Mat & dryck": ["mat", "dryck", "vin", "öl", "gastronomi", "food"],
    "Samtal & föreläsning": ["föreläsning", "samtal", "seminarium", "litteratur", "författar"],
    "Workshop & deltagande": ["workshop", "verkstad", "prova på", "öppet hus", "kurs"],
    "Nattliv & klubb": ["klubb", "nightclub", "dj", "nattliv"],
    "Natur & utomhus": ["natur", "vandring", "friluft", "fåg", "outdoor"],
    "Säsong & högtid": ["jul", "påsk", "midsommar", "halloween", "advent", "nyår"],
    "Förening & lokalsamhälle": ["förening", "hembygd", "community", "bygdegård"],
    "Student & universitet": ["universitet", "student", "campus", "disputation", "docent", "forskning"],
}

TRUSTED_SOURCES = {
    "City Örebro", "Lov Örebro", "Visit Örebro", "Visit Örebro – redaktionella eventlistor",
    "Conventum", "Örebro Konserthus", "Örebro Teater", "ÖSK Fotboll", "Örebro Hockey",
}


def _text(event):
    tags = getattr(event, "tags", None) or []
    if isinstance(tags, str):
        tags = [tags]
    return " ".join([
        getattr(event, "title", "") or "", getattr(event, "event_type", "") or "",
        getattr(event, "category", "") or "", getattr(event, "venue", "") or "", *tags,
    ]).casefold()


def classify_frontier(event):
    text = _text(event)
    hits=[]
    for segment, words in SEGMENTS.items():
        if any(word in text for word in words):
            hits.append(segment)
    return hits or ["Övrigt / ännu ej klassificerat"]


def coverage_frontier(events, *, today=None, horizons=(30,60,90)):
    today=today or date.today()
    max_h=max(horizons)
    end=today+timedelta(days=max_h)
    eligible=[]
    for event in events:
        if getattr(event, "is_demo", False):
            continue
        try: d=date.fromisoformat(event.start_date)
        except Exception: continue
        if today <= d <= end:
            eligible.append((event,d))

    rows=[]
    for segment in SEGMENTS:
        matched=[(e,d) for e,d in eligible if segment in classify_frontier(e)]
        sources=set()
        counts=Counter()
        for e,_ in matched:
            names={s.strip() for s in (getattr(e,"source_names",None) or []) if s and s.strip()}
            sources.update(names)
            counts.update(names)
        presence={h:sum(1 for _,d in matched if d <= today+timedelta(days=h)) for h in horizons}
        count30=presence.get(30,0)
        diversity=len(sources)
        if count30 >= 4 and diversity >= 2:
            status="Bra täckning"
        elif count30 > 0 or matched:
            status="Tunn"
        else:
            status="Saknas i aktuell import"
        rows.append({
            "segment":segment,
            "status":status,
            "events_30":presence.get(30,0),
            "events_60":presence.get(60,0),
            "events_90":presence.get(90,0),
            "source_diversity":diversity,
            "trusted_source_count":len(sources & TRUSTED_SOURCES),
            "single_source_dependency": bool(matched and diversity == 1),
            "sources":sorted(sources),
        })
    order={"Saknas i aktuell import":0,"Tunn":1,"Bra täckning":2}
    rows.sort(key=lambda r:(order[r["status"]], r["events_30"], r["segment"]))
    return {"events_considered":len(eligible),"rows":rows,"horizons":tuple(horizons)}
