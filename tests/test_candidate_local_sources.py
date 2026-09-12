from datetime import date
from candidate_local_sources import parse_swedish_candidate_range, parse_candidate_calendar, candidate_value_audit
from models import Event


def e(i,title,source,event_type="Konsert",start="2026-09-20"):
    return Event(id=str(i),title=title,event_type=event_type,category=event_type,start_date=start,end_date=None,start_time=None,venue="V",city="Örebro",region="Örebro",country="SE",source_names=[source])


def test_candidate_date_parsing_single_and_range():
    assert parse_swedish_candidate_range("10 september",today=date(2026,9,1)) == ("2026-09-10","2026-09-10")
    assert parse_swedish_candidate_range("28–29 september 2026",today=date(2026,9,1)) == ("2026-09-28","2026-09-29")
    assert parse_swedish_candidate_range("12 maj–15 augusti 2026",today=date(2026,1,1)) == ("2026-05-12","2026-08-15")


def test_kulturkvarteret_parser_requires_title_and_date():
    html='''<article><h3><a href="/event/broadway">Från Broadway till Duvemåla</a></h3><div>Konsert 10 september</div></article>
    <article><h3>Nyhet utan datum</h3></article>'''
    rows=parse_candidate_calendar(html,key="kulturkvarteret",today=date(2026,9,1))
    assert len(rows)==1
    assert rows[0].title=="Från Broadway till Duvemåla"
    assert rows[0].start_date=="2026-09-10"
    assert rows[0].source_names==["Kulturkvarteret"]


def test_wadkoping_range_is_one_candidate_event_not_daily_spam():
    html='''<article><h3><a href="/wadkoping/tango">Argentinsk tango</a></h3><div>Dans 1 juni–31 augusti 2026</div></article>'''
    rows=parse_candidate_calendar(html,key="wadkoping",today=date(2026,5,1))
    assert len(rows)==1
    assert rows[0].start_date=="2026-06-01"
    assert rows[0].end_date=="2026-08-31"


def test_candidate_audit_separates_unique_from_overlap():
    existing=[e(1,"Samma konsert","City Örebro"),e(2,"Annat","Conventum")]
    candidates=[e(3,"Samma konsert","Kulturkvarteret"),e(4,"Ny familjegrej","Wadköping","Familj")]
    rows=candidate_value_audit(existing,candidates)
    by={r["source"]:r for r in rows}
    assert by["Kulturkvarteret"]["overlap_events"]==1
    assert by["Kulturkvarteret"]["unique_events"]==0
    assert by["Wadköping"]["unique_events"]==1
    assert by["Wadköping"]["unique_event_types"]==["Familj"]


def test_audit_does_not_mutate_live_events():
    existing=[e(1,"Samma konsert","City Örebro")]
    candidates=[e(2,"Samma konsert","Kulturkvarteret")]
    candidate_value_audit(existing,candidates)
    assert existing[0].source_names==["City Örebro"]


def test_candidate_audit_exposes_frontier_gap_value_not_just_unique_rows():
    existing=[e(1,"Stor konsert","Conventum","Konsert")]
    museum=e(9,"Ny utställning","Örebro läns museum","Utställning")
    museum.venue="Örebro läns museum"
    rows=candidate_value_audit(existing,[museum],today=date(2026,9,1))
    row=next(r for r in rows if r["source"]=="Örebro läns museum")
    assert row["unique_events"]==1
    assert "Museum & utställning" in row["unique_frontier_segments"]
    assert "Museum & utställning" in row["underserved_segments"]
    assert row["unique_events_in_underserved_segments"]==1


def test_overlap_does_not_count_as_frontier_gap_fill():
    existing=[e(1,"Ny utställning","City Örebro","Utställning")]
    existing[0].venue="Örebro läns museum"
    candidate=e(2,"Ny utställning","Örebro läns museum","Utställning")
    candidate.venue="Örebro läns museum"
    rows=candidate_value_audit(existing,[candidate],today=date(2026,9,1))
    row=next(r for r in rows if r["source"]=="Örebro läns museum")
    assert row["overlap_events"]==1
    assert row["unique_events_in_underserved_segments"]==0
