from unittest.mock import patch
from parser_fix_evidence import analyze_gap_evidence, fetch_gap_evidence


def test_explicit_end_time_is_parser_candidate():
    r=analyze_gap_evidence('<main>Tider 19:00–22:30</main>', field='end_time', current_start_time='19:00')
    assert r['status']=='Parserkandidat' and r['value']=='22:30'


def test_duration_only_never_becomes_exact_end_time():
    r=analyze_gap_evidence('<main>Start 19:00. Längd ca 60 minuter.</main>', field='end_time', current_start_time='19:00')
    assert r['status']=='Källan saknar exakt värde'
    assert r['value'] is None


def test_explicit_age_limit_is_parser_candidate():
    r=analyze_gap_evidence('<main>Åldersgräns: 18 år</main>', field='age_limit')
    assert r['status']=='Parserkandidat'
    assert '18' in str(r['value'])


def test_unlabelled_money_is_not_price_evidence():
    r=analyze_gap_evidence('<main>Garderob 30 kr. Välkommen!</main>', field='price')
    assert r['status']=='Källan verkar sakna uppgiften'


def test_booking_is_explicitly_separate():
    r=analyze_gap_evidence('<a href="/ticket">Biljetter</a>', field='booking')
    assert r['status']=='Ej analyserad här'


def test_unsafe_url_is_rejected_without_request():
    with patch('parser_fix_evidence.requests.get') as get:
        r=fetch_gap_evidence('http://127.0.0.1/admin', field='end_time')
    assert r['kind']=='unsafe_url'
    get.assert_not_called()


def test_fetch_diagnostic_never_mutates_any_event_and_returns_result():
    class Resp:
        text='<main>Tider 19:00–22:00</main>'; status_code=200; url='https://events.example/x'
        def raise_for_status(self): pass
    with patch('parser_fix_evidence._safe_public_http_url', return_value=True), patch('parser_fix_evidence.requests.get', return_value=Resp()):
        r=fetch_gap_evidence('https://events.example/x', field='end_time', current_start_time='19:00')
    assert r['status']=='Parserkandidat' and r['value']=='22:00' and r['http_status']==200
