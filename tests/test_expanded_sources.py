from datetime import date
from unittest.mock import Mock

from expanded_sports_sources import parse_bandy_html, parse_badminton_article
from stockholm_sources import parse_stockholm_event, stockholm_events, API_URL
from taxonomy import classify
from ui_logic import event_period_matches


def stockholm_raw():
    return {'id': 'official-id', 'title': {'sv': 'Konstutställning', 'en': 'Art'},
            'city': 'Vaxholm', 'venue_name': 'Galleriet', 'url': 'konstutstallning',
            'categories': [{'slug': 'exhibitions', 'subcategories': [{'slug': 'sports'}]}],
            'location': {'latitude': 59.4, 'longitude': 18.3},
            'schedule': {'range': None, 'dates': [{'date': '2026-10-08', 'start_time': '18:00'},
                                                {'date': '2026-10-08', 'start_time': '20:00'}]}}


def test_stockholm_preserves_localized_title_city_occurrences_and_license():
    rows = parse_stockholm_event(stockholm_raw())
    assert len(rows) == 2 and rows[0].id != rows[1].id
    assert rows[0].title == 'Konstutställning'
    assert rows[0].city == 'Vaxholm' and rows[0].event_type == 'Utställning'
    assert rows[0].price_status == 'unknown' and rows[0].image_url is None
    assert rows[0].source_records[0].payload['license_url'].endswith('/by/4.0/')
    assert [x.id for x in rows] == [x.id for x in parse_stockholm_event(stockholm_raw())]


def test_stockholm_range_respects_excluded_dates_in_filters():
    raw = stockholm_raw()
    raw['schedule'] = {'range': {'start': '2026-10-07', 'end': '2026-10-10', 'excluded': ['2026-10-08']}, 'dates': []}
    row = parse_stockholm_event(raw)[0]
    assert row.start_time is None
    assert not event_period_matches(row, 'Idag', date(2026, 10, 8))
    assert event_period_matches(row, 'Idag', date(2026, 10, 9))
    assert event_period_matches(row, 'Nästa 7 dagar', date(2026, 10, 8))


def test_stockholm_invalid_dates_and_unsafe_urls_are_rejected():
    raw = stockholm_raw()
    raw['schedule']['dates'] = [{'date': '2026-02-30'}]
    assert parse_stockholm_event(raw) == []
    raw = stockholm_raw()
    raw['url'], raw['external_website_url'] = '', 'javascript:alert(1)'
    assert parse_stockholm_event(raw) == []


def test_stockholm_ongoing_range_identity_survives_api_start_date_advancing():
    raw = stockholm_raw()
    raw['schedule'] = {'range': {'start': '2026-10-07', 'end': '2026-12-31', 'excluded': []}, 'dates': []}
    before = parse_stockholm_event(raw)[0]
    raw['schedule']['range']['start'] = '2026-10-08'
    after = parse_stockholm_event(raw)[0]
    assert before.id == after.id
    assert before.source_records[0].external_id == after.source_records[0].external_id


def test_stockholm_paginates_integer_next_and_does_not_follow_foreign_url(monkeypatch):
    monkeypatch.setattr('ui_logic.local_today', lambda: date(2026, 10, 7))
    one, two = stockholm_raw(), stockholm_raw()
    two['id'] = 'second'
    responses = [Mock(json=lambda: {'count': 2, 'next': 'https://foreign.test/', 'results': [one]}),
                 Mock(json=lambda: {'count': 2, 'next': None, 'results': [two]})]
    get = Mock(side_effect=responses)
    monkeypatch.setattr('stockholm_sources.requests.get', get)
    rows, meta = stockholm_events(page_size=1)
    assert len(rows) == 4 and meta['pages_fetched'] == 2 and not meta['truncated']
    assert all(c.args[0] == API_URL for c in get.call_args_list)
    assert [c.kwargs['params']['page'] for c in get.call_args_list] == [1, 2]


def test_stockholm_marks_incomplete_import(monkeypatch):
    monkeypatch.setattr('ui_logic.local_today', lambda: date(2026, 10, 7))
    monkeypatch.setattr('stockholm_sources.requests.get', Mock(return_value=Mock(json=lambda: {'next': 2, 'results': [stockholm_raw()]})))
    _, meta = stockholm_events(max_pages=1)
    assert meta['truncated']


def test_stockholm_published_page_count_keeps_successful_pages_on_failure(monkeypatch):
    import requests
    monkeypatch.setattr('ui_logic.local_today', lambda: date(2026, 10, 7))
    def get(url, *, params, timeout):
        if params['page'] == 2:
            raise requests.Timeout('private diagnostic')
        raw = stockholm_raw()
        raw['id'] = str(params['page'])
        return Mock(json=lambda: {'count': 3, 'total_pages': 3, 'next': params['page'] + 1 if params['page'] < 3 else None, 'results': [raw]})
    monkeypatch.setattr('stockholm_sources.requests.get', get)
    rows, meta = stockholm_events()
    assert len(rows) == 4 and meta['pages_fetched'] == 2
    assert meta['failed_pages'] == 1 and meta['truncated']


def bandy_card(title='Örebro SK – Tranås BOIS', clock='14:00', url='https://orebroskbandy.ticketco.events/se/sv/e/match'):
    return f'<div class="tc-events-list--item"><a class="tc-events-list--title" href="{url}">{title}</a><div class="tc-events-list--place-time">17.10.2026 {clock} @ Örebro</div><p>Under 18 år gratis</p></div>'


def test_bandy_reads_visible_local_clock_not_jsonld_z_and_skips_season_pass():
    html = '<script type="application/ld+json">{"@type":"Event","url":"https://orebroskbandy.ticketco.events/se/nb/e/match","startDate":"2026-10-17T14:00:00Z","endDate":"2026-10-18T18:00:00Z"}</script>' + bandy_card() + bandy_card('Säsongskort 26-27')
    rows = parse_bandy_html(html)
    assert len(rows) == 1 and rows[0].start_time == '14:00'
    assert rows[0].end_date == '2026-10-18'
    assert rows[0].price_status == 'unknown'
    assert rows[0].ticket_url.endswith('/e/match')
    assert parse_bandy_html(bandy_card(url='https://foreign.test/e/match')) == []


def badminton_article(invitation='Kom och heja!', date_text='10 oktober', publication='2026-10-02'):
    return f'<article class="sa-news-detail"><article class="sa-paragraph"><div class="sa-paragraph__date">{publication} 16:00</div><div class="sa-paragraph__preamble">Lördagen {date_text} i Backahallen. {invitation}</div><div class="sa-paragraph__body"><p>10.30: Örebro– Kista (Bana 1-2)<br>16.00: Örebro– Christinehamn (Bana 1-2)</p></div></article></article>'


def test_badminton_uses_match_date_not_publication_and_keeps_opponents():
    rows = parse_badminton_article(badminton_article(), 'https://www.orebrobadminton.com/nyheter/?NID=1')
    assert len(rows) == 2
    assert rows[0].start_date == '2026-10-10' and rows[0].start_time == '10:30'
    assert rows[1].start_time == '16:00'
    assert rows[0].price_status == 'unknown'
    assert parse_badminton_article(badminton_article(invitation='Intern träning'), 'https://example.test') == []
    assert parse_badminton_article(badminton_article(publication='2026-12-28', date_text='2 januari'), 'https://example.test') == []


def test_more_sports_classified_without_turning_sports_cards_into_matches():
    for name in ['Badminton', 'Bordtennis', 'Orientering', 'Ridsport', 'Curling', 'Rugby', 'Triathlon', 'Speedway']:
        assert classify(f'{name} i Örebro').event_type == 'Sport', name
    assert classify('Hockeykort på samlarmässan').event_type != 'Sport'
