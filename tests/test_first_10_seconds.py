from ui_logic import DISCOVERY_DEFAULTS, discovery_context_label


def test_discovery_defaults_are_narrow_enough_to_feel_relevant():
    assert DISCOVERY_DEFAULTS == {
        "city": "Örebro",
        "when": "Nästa 7 dagar",
        "radius_km": 50,
        "price": "Alla priser",
    }


def test_discovery_context_label_is_compact_and_honest():
    assert discovery_context_label("Örebro", "Nästa 7 dagar", 50, "Alla priser") == "Örebro · Nästa 7 dagar · inom 50 km"
    assert discovery_context_label("Örebro", "Idag", 25, "Gratis") == "Örebro · Idag · inom 25 km · gratis"
    assert discovery_context_label("Hela Sverige", "Nästa 30 dagar", None, "Alla priser") == "Hela Sverige · Nästa 30 dagar"
