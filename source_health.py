from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class SourceHealthAssessment:
    source: str
    state: str
    imported: int
    summary: str
    issues: tuple[str, ...] = ()


# Empty results are not equally suspicious for every source. Seasonal calendars
# are allowed to be empty, while normal always-on calendars should be checked.
SEASONAL_EMPTY_SOURCES = {"Lov Örebro"}
NON_ERROR_STATES = {"OK", "Pilot", "Delvis", "Säsongstom", "Ej konfigurerad", "TESTLÄGE"}


def safe_import_error(exc: Exception) -> str:
    """Return a public/admin-safe error description without echoing URLs/secrets."""
    name = exc.__class__.__name__
    if name in {"Timeout", "ConnectTimeout", "ReadTimeout"}:
        return "Tidsgränsen för källan överskreds."
    if name in {"ConnectionError"}:
        return "Källan kunde inte nås."
    if name in {"HTTPError"}:
        return "Källan svarade med ett HTTP-fel."
    if name in {"JSONDecodeError"}:
        return "Källans svar kunde inte tolkas som förväntat."
    return "Importen misslyckades. Kontrollera källans format och tillgänglighet."


def _events_by_source(events: Iterable) -> dict[str, list]:
    result = defaultdict(list)
    for event in events:
        for source in getattr(event, "source_names", []) or []:
            result[str(source)].append(event)
    return result


def assess_source_health(source_rows: Sequence[Sequence], events: Iterable) -> list[SourceHealthAssessment]:
    """Turn raw import rows into actionable, conservative source diagnostics.

    The function only diagnoses what can be observed in the current import. It does
    not claim that a source has broken merely because volume changed historically;
    historical baselines require scheduled imports/background persistence later.
    """
    grouped = _events_by_source(events)
    assessments = []

    for row in source_rows:
        source, status, imported, comment = row
        imported = int(imported or 0)
        source_events = grouped.get(source, [])
        issues = []

        if status == "Fel" or status not in NON_ERROR_STATES:
            state = "Fel"
            issues.append("Importen misslyckades")
        elif status == "Ej konfigurerad":
            state = "Ej konfigurerad"
        elif status == "Säsongstom" or (imported == 0 and source in SEASONAL_EMPTY_SOURCES):
            state = "Säsongstom"
        elif imported == 0:
            state = "Kontrollera"
            issues.append("0 importerade event från en normalt aktiv källa")
        elif status == "Delvis":
            state = "Delvis"
            issues.append("Importen nådde en säkerhetsgräns och kan vara ofullständig")
        elif status == "Pilot":
            state = "Pilot"
        else:
            state = "OK"

        if source_events:
            missing_url = sum(not (getattr(e, "official_url", None) or getattr(e, "ticket_url", None)) for e in source_events)
            missing_city = sum(not str(getattr(e, "city", "") or "").strip() for e in source_events)
            missing_date = sum(not str(getattr(e, "start_date", "") or "").strip() for e in source_events)
            n = len(source_events)

            # These checks are intentionally high-threshold. A warning should indicate
            # a likely parser/data regression, not merely ordinary incomplete metadata.
            if missing_date:
                issues.append(f"{missing_date}/{n} event saknar startdatum")
                state = "Kontrollera" if state in {"OK", "Pilot"} else state
            if n >= 3 and missing_url / n >= 0.80:
                issues.append(f"{missing_url}/{n} event saknar käll-/biljettlänk")
                state = "Kontrollera" if state in {"OK", "Pilot"} else state
            if n >= 3 and missing_city / n >= 0.80:
                issues.append(f"{missing_city}/{n} event saknar ort")
                state = "Kontrollera" if state in {"OK", "Pilot"} else state

        summary = "; ".join(issues) if issues else str(comment or "Inga avvikelser upptäckta i aktuell import")
        assessments.append(SourceHealthAssessment(source, state, imported, summary, tuple(issues)))

    return assessments


def source_health_summary(assessments: Sequence[SourceHealthAssessment]) -> dict:
    counts = defaultdict(int)
    for item in assessments:
        counts[item.state] += 1
    degraded = [x for x in assessments if x.state in {"Fel", "Kontrollera"}]
    return {
        "counts": dict(counts),
        "degraded": degraded,
        "has_public_warning": any(x.state == "Fel" for x in degraded) or len(degraded) >= 2,
    }
