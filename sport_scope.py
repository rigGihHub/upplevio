"""Discovery's sport selection: identified team sports, with badminton excluded."""
import re


TEAM_SPORT_PATTERN = re.compile(
    r"\b(?:fotboll(?:s\w+)?|soccer|football|futsal|ishockey|ice hockey|hockey|shl|hockeyallsvenskan|"
    r"basket(?:boll|ball)?|handboll|handball|volley(?:boll|ball)?|innebandy|floorball|bandy|"
    r"rugby|curling|baseboll|baseball|softboll|softball|cricket|vattenpolo|water polo|lacrosse|kabaddi|"
    r"counter[ -]strike|league of legends|dota 2)\b",
    re.I,
)
INDIVIDUAL_SPORT_PATTERN = re.compile(
    r"\b(?:badminton\w*|bordtennis|table tennis|tennis|padel|golf|friidrott|athletics|"
    r"löpning|running|maraton|marathon|triathlon|triatlon|orientering|orienteering|"
    r"cykel(?:lopp|tävling)?|cycling|simning|swimming|skidor|skiing|"
    r"motorsport|rally|speedway|motocross|gokart|ridsport|dressyr|hästhoppning|"
    r"kampsport|boxing|boxning|judo|karate|taekwondo|brottning|gymnastik|gymnastics|"
    r"kajak\w*|kayak\w*|paddling|skridskor|skridskoåkning|konståkning|"
    r"yoga|pilates|fitness|vandring|hiking|klättring|climbing|fäktning|fencing)\b",
    re.I,
)
SPORT_TYPES = {"sport", "sports", "sport & hälsa", "sports & wellbeing", "sports & well-being"}
CULTURE_TYPES = {"konsert", "teater", "show", "stand-up", "dans", "scen & film", "utställning", "föreläsning", "marknad", "mässa"}
TEAM_LEAGUE_PATTERN = re.compile(r"\b(?:allsvenskan(?:s)?|superettan|elitettan)\b", re.I)


def sport_allowed_in_discovery(event):
    """Preserve other event types; show sports only with actual team-sport evidence.

    Titles/categories/tags take precedence over incidental description mentions.
    Generic 'Sport' or 'lagmatch' alone cannot establish the discipline.
    """
    title = getattr(event, "title", "") or ""
    event_type = (getattr(event, "event_type", "") or "").casefold().strip()
    category = (getattr(event, "category", "") or "").casefold().strip()
    tags = getattr(event, "tags", []) or []
    if isinstance(tags, str):
        tags = [tags]
    metadata = " ".join([category, *tags])
    explicit_sport = event_type in SPORT_TYPES or category in SPORT_TYPES
    if not explicit_sport and event_type in CULTURE_TYPES:
        return True
    sports_event = explicit_sport or any(tag.casefold() in SPORT_TYPES for tag in tags)
    sports_event = sports_event or bool(TEAM_SPORT_PATTERN.search(title + " " + metadata) or INDIVIDUAL_SPORT_PATTERN.search(title + " " + metadata))
    if not sports_event:
        return True
    if INDIVIDUAL_SPORT_PATTERN.search(title + " " + metadata):
        return False
    if TEAM_SPORT_PATTERN.search(title + " " + metadata):
        return True
    description = getattr(event, "description", "") or ""
    if INDIVIDUAL_SPORT_PATTERN.search(description):
        return False
    return bool(TEAM_SPORT_PATTERN.search(description) or (TEAM_LEAGUE_PATTERN.search(title + " " + description) and re.search(r"\w\s*[-–]\s*\w", title)))
