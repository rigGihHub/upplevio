
from dataclasses import dataclass

@dataclass(frozen=True)
class AdSlot:
    key: str
    surface: str
    format: str
    max_per_view: int
    enabled: bool = False

# Inventory is intentionally disabled. These are integration points for a future
# provider such as AdSense; Upplevio must not optimize discovery for ad impressions.
AD_SLOTS = (
    AdSlot("discovery_native_1", "discovery", "native", 1, False),
    AdSlot("discovery_display_footer", "discovery", "display", 1, False),
)

def enabled_slots(surface: str):
    return [x for x in AD_SLOTS if x.surface == surface and x.enabled]
