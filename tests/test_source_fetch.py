import time

from source_fetch import SourceTask, run_source_tasks


def test_source_failure_does_not_discard_other_source_results():
    def good():
        return ["event"], [("Bra källa", "OK", 1, "ok")]
    def broken():
        raise RuntimeError("secret=https://example.test/?token=do-not-leak")

    results = run_source_tasks([
        SourceTask("good", "Bra källa", good),
        SourceTask("bad", "Trasig källa", broken),
    ], max_workers=2)

    assert results[0].events == ["event"]
    assert results[1].events == []
    assert results[1].health[0][0:3] == ("Trasig källa", "Fel", 0)
    assert "do-not-leak" not in results[1].health[0][3]


def test_independent_sources_start_without_waiting_for_previous_source():
    starts = {}

    def fetch(name, delay):
        def inner():
            starts[name] = time.monotonic()
            time.sleep(delay)
            return [], [(name, "OK", 0, "test")]
        return inner

    run_source_tasks([
        SourceTask("slow", "Slow", fetch("slow", 0.08)),
        SourceTask("fast", "Fast", fetch("fast", 0.01)),
    ], max_workers=2)

    assert abs(starts["slow"] - starts["fast"]) < 0.06


def test_results_keep_configured_source_order_even_when_completion_order_differs():
    def fetch(name, delay):
        def inner():
            time.sleep(delay)
            return [name], [(name, "OK", 1, "test")]
        return inner

    results = run_source_tasks([
        SourceTask("first", "First", fetch("first", 0.03)),
        SourceTask("second", "Second", fetch("second", 0.0)),
    ], max_workers=2)
    assert [r.key for r in results] == ["first", "second"]
