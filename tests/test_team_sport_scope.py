from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import db
import engagement
import sources
from models import Event
from source_registry import source_by_key
from sport_scope import sport_allowed_in_discovery
from ui_logic import local_today


def event(title, event_type='Sport', category='Sport', tags=None, description=''):
    return SimpleNamespace(title=title, event_type=event_type, category=category,
                           tags=tags or [], description=description)


@pytest.mark.parametrize('sport', ['Fotboll', 'Amerikansk fotboll', 'Ishockey', 'Bandy', 'Basket', 'Handboll',
                                  'Volleyboll', 'Innebandy', 'Rugby', 'Curling', 'Baseball', 'Cricket', 'Vattenpolo'])
def test_identified_team_sports_remain_visible(sport):
    assert sport_allowed_in_discovery(event(f'{sport}: hemmamatch'))


@pytest.mark.parametrize('sport', ['Badminton', 'Badmintonturnering', 'Tennis', 'Padel', 'Golf', 'Bordtennis',
                                  'Maraton', 'Triathlon', 'Orientering', 'Speedway', 'Judo', 'Kajak', 'Yoga'])
def test_individual_sports_are_hidden(sport):
    assert not sport_allowed_in_discovery(event(f'{sport}: tävling'))


def test_badminton_league_match_is_excluded_even_when_called_team_match():
    assert not sport_allowed_in_discovery(event('Örebro – Kista', tags=['Badminton'], description='Lagmatch i division 1'))


def test_generic_ticketmaster_sports_record_uses_genre_and_tags():
    assert not sport_allowed_in_discovery(event('Finalen', event_type='Evenemang', category='Tennis', tags=['Sports']))
    assert sport_allowed_in_discovery(event('Djurgården – AIK', event_type='Evenemang', category='Soccer', tags=['Sports']))


def test_source_description_can_identify_team_sport_but_unknown_sport_is_hidden():
    assert sport_allowed_in_discovery(event('Djurgården – AIK', description='En fotbollsmatch på hemmaplan.'))
    assert not sport_allowed_in_discovery(event('Finalen', description='Lagmatch i mästerskapet.'))
    assert not sport_allowed_in_discovery(event('Finalen', description='Badminton i en hall där även fotboll spelas.'))


def test_team_league_fixture_without_explicit_discipline_is_preserved():
    assert sport_allowed_in_discovery(event('AIK – IF Brommapojkarna - Allsvenskan 2026'))
    assert not sport_allowed_in_discovery(event('Örebro – Kista - Allsvenskan', description='Lagbadminton är badminton mellan klubbar.'))
    assert not sport_allowed_in_discovery(event('Allsvenskan', description='En tävlingsserie.'))


def test_identified_team_esports_are_preserved_but_generic_gaming_is_not_sport_evidence():
    assert sport_allowed_in_discovery(event('Svenska Cupen i Counter-Strike', tags=['Gaming']))
    assert not sport_allowed_in_discovery(event('Gamingfinalen', description='Mästerskap i tv-spel.'))


def test_specific_individual_sport_overrides_incidental_team_sport_mention():
    assert not sport_allowed_in_discovery(event('Badminton i Örebro', description='Klubben erbjuder även fotboll.'))
    assert sport_allowed_in_discovery(event('Fotboll i Örebro', description='Arenan har tidigare använts för tennis.'))


def test_concerts_and_exhibitions_are_preserved_despite_incidental_sport_mentions():
    assert sport_allowed_in_discovery(event('En konsert', event_type='Konsert', category='Musik', tags=['Sport'], description='Artisten gillar golf.'))
    assert sport_allowed_in_discovery(event('Hockeykort på mässan', event_type='Mässa', category='Samlarkort'))
    assert sport_allowed_in_discovery(event('Konstutställning', event_type='Utställning', category='Konst'))
    assert not sport_allowed_in_discovery(event('Familjepaddling med kajak', event_type='Familj', category='Familj', tags=['Sport', 'Kajak']))


def test_badminton_source_is_not_scheduled_for_import(monkeypatch):
    seen = []
    def capture(tasks):
        seen.extend(task.key for task in tasks)
        return []
    monkeypatch.setattr('source_fetch.run_source_tasks', capture)
    sources.load_events()
    assert 'osk_bandy' in seen and 'visitstockholm' in seen
    assert 'orebro_badminton' not in seen
    assert not source_by_key('orebro_badminton').enabled_by_default


def test_app_hides_individual_sports_in_discovery_saved_and_fallback(monkeypatch, tmp_path):
    st.cache_data.clear()
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'events.db')
    monkeypatch.setattr(engagement, 'TRACKING_DB', tmp_path / 'engagement.db')
    day = (local_today() + timedelta(days=1)).isoformat()
    def sample(id, title, kind, category, tags):
        return Event(id=id, title=title, event_type=kind, category=category,
                     start_date=day, end_date=None, start_time='12:00', venue='Testarena',
                     city='Örebro', region='Örebro', country='Sverige', tags=tags, source_names=['Testkälla'])
    rows = [sample('bandy', 'Bandy: hemmamatch', 'Sport', 'Sport', ['Bandy']),
            sample('badminton', 'Badminton: Örebro – Kista', 'Sport', 'Sport', ['Badminton']),
            sample('tennis', 'Tennis: final', 'Evenemang', 'Tennis', ['Sports']),
            sample('concert', 'Konsert med Testbandet', 'Konsert', 'Musik', [])]
    monkeypatch.setattr(sources, 'load_events', lambda *args, **kwargs: (rows, []))
    for row in rows:
        db.toggle_favorite(row.id)
    try:
        app = AppTest.from_file(Path(__file__).resolve().parents[1] / 'app.py', default_timeout=10).run()
        assert not app.exception
        cards = '\n'.join(m.value for m in app.markdown if 'event-title' in m.value and '<style>' not in m.value)
        assert 'Bandy: hemmamatch' in cards and 'Konsert med Testbandet' in cards
        assert 'Badminton:' not in cards and 'Tennis: final' not in cards
        type_widget = next(x for x in app.selectbox if 'Vad?' in x.label)
        type_widget.select('Sport').run()
        assert not app.exception
        assert any('result-summary"><b>1</b> event' in m.value for m in app.markdown)
        # Today's empty view suggests tomorrow, using the same restricted pool.
        app.selectbox(key='discover_when').select('Idag').run()
        assert not app.exception
        fallback = '\n'.join(m.value for m in app.markdown)
        assert 'Bandy: hemmamatch' in fallback
        assert 'Badminton: Örebro' not in fallback and 'Tennis: final' not in fallback
        app.radio(key='active_view').set_value('Sparat').run()
        assert not app.exception
        saved = '\n'.join(m.value for m in app.markdown)
        assert 'Bandy: hemmamatch' in saved and 'Konsert med Testbandet' in saved
        assert 'Badminton: Örebro' not in saved and 'Tennis: final' not in saved
    finally:
        st.cache_data.clear()
