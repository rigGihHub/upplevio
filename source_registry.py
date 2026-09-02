from dataclasses import dataclass
from typing import Optional, List

@dataclass(frozen=True)
class SourceDefinition:
    key: str
    name: str
    source_type: str
    coverage: str
    country: str
    city: Optional[str]
    url: str
    trust_level: str
    import_mode: str
    enabled_by_default: bool
    notes: str

SOURCES: List[SourceDefinition] = [
    SourceDefinition(key="showtic",name="Showtic",source_type="ticketing_calendar",coverage="Stand-up, musikal, teater och show",country="Sverige",city=None,url="https://showtic.se/forestallningar/stand-up",trust_level="high",import_mode="html_calendar",enabled_by_default=False,notes="Kompletterande svensk scenkälla; parser experimentell."),


    SourceDefinition(
        key="kortcentralen",
        name="Kortcentralen",
        source_type="specialist_calendar",
        coverage="Samlarkort, TCG och sportkortsmässor",
        country="Sverige", city=None,
        url="https://kortcentralen.se/event-handelser",
        trust_level="medium_high",
        import_mode="html_calendar",
        enabled_by_default=False,
        notes="Specialiserad svensk samlarkortskalender. Stark discovery-källa, men bör verifieras mot arrangör/Tickster."
    ),
    SourceDefinition(
        key="tickster_collectors",
        name="Tickster – samlare/retro",
        source_type="ticketing_search",
        coverage="RetroMania, Samlarkortfestivalen och närliggande event",
        country="Sverige", city=None,
        url="https://www.tickster.com/se/sv/events/search",
        trust_level="high",
        import_mode="html_search",
        enabled_by_default=False,
        notes="Biljettkälla med flera relevanta svenska samlar- och retroevent. Parser experimentell."
    ),

    SourceDefinition(
        key="ticketmaster",
        name="Ticketmaster",
        source_type="api",
        coverage="Konserter och biljettevenemang",
        country="Sverige", city=None,
        url="https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/",
        trust_level="high",
        import_mode="api",
        enabled_by_default=True,
        notes="Primär livekälla när API-nyckel finns."
    ),
    SourceDefinition(
        key="visitsweden",
        name="Visit Sweden",
        source_type="api",
        coverage="Bred svensk eventdata",
        country="Sverige", city=None,
        url="https://data.visitsweden.com/store/search",
        trust_level="high",
        import_mode="jsonld",
        enabled_by_default=True,
        notes="Publik länkad eventdata. Kräver defensiv normalisering."
    ),
    SourceDefinition(
        key="stockholmsmassan",
        name="Stockholmsmässan",
        source_type="official_venue",
        coverage="Mässor, kongresser och event",
        country="Sverige", city="Stockholm",
        url="https://stockholmsmassan.se/kalender/",
        trust_level="high",
        import_mode="html_calendar",
        enabled_by_default=False,
        notes="Officiell kalender. Experimentell parser tills liveformat verifierats."
    ),
    SourceDefinition(
        key="elmia",
        name="Elmia",
        source_type="official_venue",
        coverage="Mässor och större event",
        country="Sverige", city="Jönköping",
        url="https://www.elmia.se/hela-kalendern/",
        trust_level="high",
        import_mode="html_calendar",
        enabled_by_default=False,
        notes="Officiell kalender med kalenderexport per event."
    ),
    SourceDefinition(
        key="svenska_massan",
        name="Svenska Mässan Gothia Towers",
        source_type="official_venue",
        coverage="Mässor och event",
        country="Sverige", city="Göteborg",
        url="https://svenskamassan.se/utforska-oss/kalender/",
        trust_level="high",
        import_mode="html_calendar",
        enabled_by_default=False,
        notes="Officiell kalender. Parser behöver verifieras innan autoimport."
    ),
    SourceDefinition(
        key="malmomassan",
        name="Malmömässan",
        source_type="official_venue",
        coverage="Mässor och event",
        country="Sverige", city="Malmö",
        url="https://www.malmomassan.se/calendar/",
        trust_level="high",
        import_mode="html_calendar",
        enabled_by_default=False,
        notes="Officiell kalender. Experimentell parser finns."
    ),
]

def source_by_key(key: str):
    return next((s for s in SOURCES if s.key == key), None)
