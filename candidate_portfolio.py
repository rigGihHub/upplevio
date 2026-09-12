"""Portfolio view for candidate sources.

This module deliberately avoids a weighted source score. It consolidates the
existing candidate history into an operational priority so maintainers can
see which parsers deserve attention, which need more observations, and which
should be deprioritised. CandidateDecision remains the activation authority.
"""
from dataclasses import dataclass
from statistics import median

from candidate_decision import candidate_history, candidate_decisions


@dataclass(frozen=True)
class CandidatePortfolioRow:
    source: str
    priority: str
    evidence: str
    reasons: tuple[str, ...]
    snapshots: int
    distinct_days: int
    parser_success_rate: float | None
    median_unique_events: float | None
    median_unique_share: float | None
    median_gap_events: float | None
    zero_unique_success_rate: float | None
    activation_decision: str


def _median(values):
    values=list(values)
    return float(median(values)) if values else None


def _evidence(days: int, snapshots: int) -> str:
    if days >= 4 and snapshots >= 4:
        return "Stabilare underlag"
    if days >= 3 and snapshots >= 3:
        return "Aktiveringsbart underlag"
    if days >= 2:
        return "Växande underlag"
    return "För lite underlag"


def candidate_portfolio(*, db_path=None):
    history=candidate_history(db_path=db_path)
    decisions={d.source:d for d in candidate_decisions(db_path=db_path)}
    sources=sorted({r["source"] for r in history})
    rows=[]

    for source in sources:
        source_rows=[r for r in history if r.get("source")==source]
        days=len({r.get("snapshot_day") for r in source_rows if r.get("snapshot_day")})
        successes=[r for r in source_rows if str(r.get("status","")).casefold()=="ok"]
        success_rate=(len(successes)/len(source_rows)) if source_rows else None
        unique_values=[int(r.get("unique_events") or 0) for r in successes]
        shares=[float(r["unique_share"]) for r in successes if r.get("unique_share") is not None]
        gap_values=[int(r.get("unique_events_in_underserved_segments") or 0) for r in successes]
        med_unique=_median(unique_values)
        med_share=_median(shares)
        med_gap=_median(gap_values)
        zero_unique_rate=(sum(1 for v in unique_values if v == 0)/len(unique_values)) if unique_values else None
        decision=decisions.get(source)
        activation=decision.decision if decision else "Fortsätt mäta"
        reasons=[]

        # Activation authority stays with CandidateDecision; portfolio only sets work priority.
        if activation == "Aktivera":
            priority="Aktiveringskandidat"
            reasons.append("Kandidatmotorn har tillräckligt återkommande evidens för aktivering.")
        elif activation == "Avstå":
            priority="Låg prioritet"
            reasons.append("Kandidatmotorn rekommenderar att källan avstås efter upprepade mätningar.")
        elif len(source_rows) >= 4 and success_rate is not None and success_rate < 0.80:
            priority="Parserproblem"
            reasons.append(f"Parsern har bara lyckats i {success_rate*100:.0f}% av mätningarna.")
        elif days >= 4 and zero_unique_rate is not None and zero_unique_rate >= 0.75 and (med_gap or 0) == 0:
            priority="Låg prioritet"
            reasons.append("Källan har gett noll unika event i minst 75% av lyckade mätningar.")
            reasons.append("Ingen återkommande unik nytta i tunn/saknad Coverage Frontier har observerats.")
        elif days >= 3 and (med_gap or 0) >= 1:
            priority="Prioritera mätning"
            reasons.append("Källan tillför unika event i segment där aktuell import är tunn eller saknas.")
        elif days >= 3 and ((med_unique or 0) >= 2 or (med_share or 0) >= 0.30):
            priority="Prioritera mätning"
            reasons.append("Källan visar återkommande unik nytta men har ännu inget aktiveringsbeslut.")
        else:
            priority="Fortsätt mäta"
            reasons.append("Underlaget räcker ännu inte för att höja eller sänka källans arbetsprioritet.")

        if med_unique is not None:
            reasons.append(f"Median unika event: {med_unique:.0f}.")
        if med_share is not None:
            reasons.append(f"Median unik andel: {med_share*100:.0f}%.")
        if med_gap is not None and med_gap > 0:
            reasons.append(f"Median unika gap-event: {med_gap:.0f}.")

        rows.append(CandidatePortfolioRow(
            source=source,
            priority=priority,
            evidence=_evidence(days,len(source_rows)),
            reasons=tuple(reasons),
            snapshots=len(source_rows),
            distinct_days=days,
            parser_success_rate=success_rate,
            median_unique_events=med_unique,
            median_unique_share=med_share,
            median_gap_events=med_gap,
            zero_unique_success_rate=zero_unique_rate,
            activation_decision=activation,
        ))

    order={"Aktiveringskandidat":0,"Prioritera mätning":1,"Parserproblem":2,"Fortsätt mäta":3,"Låg prioritet":4}
    rows.sort(key=lambda r:(order.get(r.priority,9), -(r.median_gap_events or 0), -(r.median_unique_events or 0), r.source.casefold()))
    return rows
