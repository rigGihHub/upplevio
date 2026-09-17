"""Source coverage priorities for Upplevio v0.92.

Kept separate from runtime loading until each adapter has parser tests and
failure isolation. This prevents an experimental source from breaking live.
"""

SOURCE_COVERAGE_TARGETS = [
    {
        "key": "visitorebro_calendar",
        "name": "Visit Örebro evenemangskalender",
        "region": "Örebro",
        "categories": ["Konsert", "Marknad", "Mässa", "Teater", "Sport", "Familj"],
        "priority": 100,
        "status": "adapter_next",
        "reason": "Broad local calendar; first choice for filling general discovery gaps.",
    },
    {
        "key": "kulturkvarteret",
        "name": "Kulturkvarteret",
        "region": "Örebro",
        "categories": ["Konsert", "Teater", "Familj", "Utställning", "Föreläsning"],
        "priority": 90,
        "status": "candidate",
        "reason": "High-value local culture and family programme.",
    },
    {
        "key": "city_orebro",
        "name": "City Örebro",
        "region": "Örebro",
        "categories": ["Marknad", "Familj", "Musik", "Övrigt"],
        "priority": 80,
        "status": "candidate",
        "reason": "Complements tourism and ticketing sources with city-centre activity.",
    },
    {
        "key": "local_sports",
        "name": "Lokala officiella sportkällor",
        "region": "Örebro",
        "categories": ["Fotboll", "Ishockey", "Basket", "Handboll", "Innebandy", "Volleyboll", "Amerikansk fotboll"],
        "priority": 95,
        "status": "expand",
        "reason": "Official club/league schedules are needed because generic event feeds miss matches.",
    },
]


def prioritized_targets():
    return sorted(SOURCE_COVERAGE_TARGETS, key=lambda item: (-item["priority"], item["name"]))
