from ui_performance import (
    INITIAL_RESULT_LIMIT,
    clamp_result_limit,
    next_result_limit,
    remaining_result_count,
    result_filter_signature,
)


def test_initial_limit_caps_large_lists_but_not_small_lists():
    assert clamp_result_limit(100) == INITIAL_RESULT_LIMIT
    assert clamp_result_limit(7) == 7


def test_show_more_never_exceeds_total():
    assert next_result_limit(100, 12) == 24
    assert next_result_limit(19, 12) == 19


def test_remaining_count_is_never_negative():
    assert remaining_result_count(100, 24) == 76
    assert remaining_result_count(10, 12) == 0


def test_filter_signature_is_stable_for_interest_order_and_query_whitespace():
    a = result_filter_signature(
        origin_city="Örebro", when="Nästa 7 dagar", radius_km=50,
        price_filter="Alla priser", query="  hockey ", type_filter="Alla",
        only_new=False, interests=["Sport", "Familj"],
    )
    b = result_filter_signature(
        origin_city="Örebro", when="Nästa 7 dagar", radius_km=50,
        price_filter="Alla priser", query="hockey", type_filter="Alla",
        only_new=False, interests=["Familj", "Sport"],
    )
    assert a == b


def test_event_id_signature_is_order_independent_and_deduplicated():
    from ui_performance import event_id_signature
    assert event_id_signature(["b", "a", "a"]) == event_id_signature(["a", "b"])
    assert event_id_signature(["a"]) != event_id_signature(["b"])
