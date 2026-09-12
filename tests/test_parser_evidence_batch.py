from parser_evidence_batch import evidence_batch_audit


def cases(n=5):
    return [{"event_id":str(i),"title":f"E{i}","date":"2026-09-20","url":f"https://x.test/{i}","start_time":"19:00","attribution":"Enkällsevent","clean_attribution":True} for i in range(n)]

def test_batch_detects_recurring_parser_candidate():
    def fetch(url, **kwargs):
        return {"status":"Parserkandidat","kind":"explicit_time","value":"22:00","snippet":"19-22","explanation":"x","http_status":200}
    r=evidence_batch_audit(cases(5), field="end_time", fetcher=fetch)
    assert r["classification"] == "Återkommande parserkandidat"
    assert r["parser_candidates"] == 5
    assert r["candidate_rate"] == 1.0

def test_batch_excludes_fetch_failures_from_rate():
    def fetch(url, **kwargs):
        if url.endswith('/0'):
            return {"status":"Kunde inte granska","kind":"fetch_error","value":None,"snippet":"","explanation":"x","http_status":500}
        return {"status":"Parserkandidat","kind":"explicit_time","value":"22:00","snippet":"","explanation":"x","http_status":200}
    r=evidence_batch_audit(cases(4), field="end_time", fetcher=fetch)
    assert r["analyzable"] == 3
    assert r["candidate_rate"] == 1.0

def test_batch_no_parser_trend_when_source_lacks_field():
    def fetch(url, **kwargs):
        return {"status":"Källan verkar sakna uppgiften","kind":"not_found","value":None,"snippet":"","explanation":"x","http_status":200}
    r=evidence_batch_audit(cases(4), field="age_limit", fetcher=fetch)
    assert r["classification"] == "Ingen parsertrend hittad"

def test_batch_needs_three_analyzable_cases():
    def fetch(url, **kwargs):
        return {"status":"Parserkandidat","kind":"explicit","value":1,"snippet":"","explanation":"x","http_status":200}
    r=evidence_batch_audit(cases(2), field="price", fetcher=fetch)
    assert r["classification"] == "För lite evidens"

def test_batch_respects_limit_and_empty_urls():
    c=cases(5); c.insert(0,{"event_id":"z","url":"","clean_attribution":True})
    def fetch(url, **kwargs):
        return {"status":"Källan verkar sakna uppgiften","kind":"not_found","value":None,"snippet":"","explanation":"x","http_status":200}
    r=evidence_batch_audit(c, field="door_time", limit=3, fetcher=fetch)
    assert r["requested"] == 3
    assert len(r["rows"]) == 3
