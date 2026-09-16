import re
from dataclasses import dataclass, field
from typing import List, Set

@dataclass
class Classification:
    event_type: str
    category: str
    tags: List[str] = field(default_factory=list)

# Multi-label taxonomy: broad enough for discovery, conservative enough to avoid
# turning generic words into a confident event type.
RULES = {
    "Stand-up": [r"\bstand[\s-]?up\b", r"\bkomiker\b", r"\bcomedy\b", r"\bhumor\b"],
    "Samlarkort": [r"\bsamlarkort\b", r"\bsamlarbilder\b", r"\btrading cards?\b", r"\bcard show\b", r"\btcg\b", r"\bpok[ée]mon\b", r"\byu[\s-]?gi[\s-]?oh\b", r"\blorcana\b", r"\bmagic(?: the gathering)?\b", r"\bone piece\b"],
    "Sportkort": [r"\bhockeykort\b", r"\bfotbollskort\b", r"\bsportkort\b", r"\bsports cards?\b"],
    "Retro & nostalgi": [r"\bretro\b", r"\bnostalgi\b", r"\b80[\s-]?tal\b", r"\b90[\s-]?tal\b", r"\bretromania\b"],
    "Gaming": [r"\bgaming\b", r"\btv[\s-]?spel\b", r"\bnintendo\b", r"\bsega\b", r"\bplaystation\b", r"\bxbox\b", r"\besport\b", r"\be-sport\b"],
    "Comic/anime": [r"\bcomic\b", r"\bcomics\b", r"\banime\b", r"\bmanga\b", r"\bcosplay\b"],
    "Lego": [r"\blego\b", r"\bklossfestival"],
    "Leksaker": [r"\bleksak", r"\btoy\b", r"\bbarbie\b", r"\bhe[\s-]?man\b"],
    "Teknik": [r"\btech\b", r"\bteknik\b", r"\btechnology\b"],
    "Industri": [r"\bindustri\b", r"\bindustrial\b", r"\btillverkning\b"],
    "Miljö & hållbarhet": [r"\bmiljö\b", r"\bhållbar", r"\bavfall\b", r"\brecycling\b", r"\bcircular\b"],
    "Fordon": [r"\bfordon\b", r"\bautomotive\b", r"\bbilmässa\b", r"\bmotor\b", r"\brally\b", r"\bmotorsport\b"],
    "Mat & dryck": [r"\bmatfestival\b", r"\bfood festival\b", r"\bmatmarknad\b", r"\bvinmässa\b", r"\bölmässa\b", r"\bstreet food\b"],
    "Teater": [r"\bteater\b", r"\btheatre\b", r"\bdrama\b", r"\bskådespel\b"],
    "Musikal/show": [r"\bmusikal\b", r"\bmusical\b", r"\bshow\b", r"\brevy\b", r"\bcirkus\b"],
    "Dans": [r"\bdansföreställning\b", r"\bbalett\b", r"\bdance show\b"],
    "Konsert": [r"\bkonsert\b", r"\bconcert\b", r"\blive music\b", r"\bgig\b"],
    "Festival": [r"\bfestival\b"],
    "Marknad": [r"\bmarknad\b", r"\bloppis\b", r"\bflea market\b", r"\bjulmarknad\b", r"\bmatmarknad\b"],
    "Utställning": [r"\butställning\b", r"\bexhibition\b", r"\bvernissage\b", r"\bkonsthall\b"],
    "Föreläsning": [r"\bföreläsning\b", r"\blecture\b", r"\bförfattarsamtal\b", r"\bsamtalskväll\b"],
    "Familj": [r"\bfamiljeföreställning\b", r"\bfamiljedag\b", r"\bbarnteater\b", r"\bbarnföreställning\b", r"\bför barn\b"],
    "Sport": [
        r"\bsportevent\b", r"\bmästerskap\b", r"\bchampionship\b", r"\bfotboll\b", r"\bsoccer\b",
        r"\bishockey\b", r"\bhockey\b", r"\bshl\b", r"\bhockeyallsvenskan\b", r"\bbasket\b", r"\bhandboll\b",
        r"\binnebandy\b", r"\bvolleyboll\b", r"\bvolleyball\b", r"\bbandy\b", r"\btennis\b", r"\bpadel\b",
        r"\bfriidrott\b", r"\bathletics\b", r"\blöpning\b", r"\bmaraton\b", r"\bmarathon\b", r"\bcykel\b",
        r"\bcycling\b", r"\bsimning\b", r"\bswimming\b", r"\bskidor\b", r"\bskiing\b", r"\bgolf\b",
        r"\bamerikansk fotboll\b", r"\bamerican football\b", r"\bsuperettan\b", r"\belitettan\b",
        r"\ballsvenskan\b", r"\bsvenska cupen\b", r"\börebro sk\b", r"\börebro hockey\b"
    ],
}

EVENT_TYPE_PRIORITY = [
    ("Stand-up", "Stand-up"), ("Teater", "Teater"), ("Musikal/show", "Show"),
    ("Dans", "Dans"), ("Konsert", "Konsert"), ("Sport", "Sport"),
    ("Marknad", "Marknad"), ("Utställning", "Utställning"),
    ("Föreläsning", "Föreläsning"), ("Familj", "Familj"),
]

COLLECTOR_TAGS = {"Samlarkort","Sportkort","Retro & nostalgi","Gaming","Comic/anime","Lego","Leksaker"}

def classify(title: str, description: str = "", existing_type: str = "Evenemang", existing_category: str = "Okategoriserat"):
    text = f"{title} {description}".lower()
    tags: Set[str] = set()
    for tag, patterns in RULES.items():
        if any(re.search(p, text, re.I) for p in patterns):
            tags.add(tag)

    event_type = existing_type or "Evenemang"
    category = existing_category or "Okategoriserat"

    for tag, mapped_type in EVENT_TYPE_PRIORITY:
        if tag in tags:
            # Keep a specific trusted upstream type, but upgrade generic buckets.
            if event_type in ("Evenemang", "Event", "Okänt", "Okategoriserat", ""):
                event_type = mapped_type
            if category in ("Okategoriserat", "Evenemang", "", None):
                category = tag
            break
    else:
        if tags & COLLECTOR_TAGS:
            event_type = "Mässa" if any(x in text for x in ["mässa","festival","show","expo","retromania","samlarkortsfestival"]) else event_type
            if "Samlarkort" in tags:
                category = "Samlarkort"
            elif "Retro & nostalgi" in tags:
                category = "Retro & nostalgi"
        elif existing_category in ("Okategoriserat","Evenemang") and tags:
            category = sorted(tags)[0]

    return Classification(event_type=event_type, category=category, tags=sorted(tags))

def collector_subcategories():
    return ["Alla samlare", "Samlarkort", "Sportkort", "Pokémon / TCG", "Retro & nostalgi", "Gaming", "Comic/anime", "Lego", "Leksaker"]

def collector_match(event, subcategory="Alla samlare"):
    hay = " ".join([event.title,event.description,event.category,*event.tags]).lower()
    if subcategory == "Alla samlare":
        return any(x.lower() in hay for x in COLLECTOR_TAGS) or event.category in COLLECTOR_TAGS
    if subcategory == "Pokémon / TCG":
        needles = ["pokémon","pokemon","tcg","magic","yu-gi-oh","lorcana","one piece"]
        return any(n in hay for n in needles)
    return subcategory.lower() in hay
