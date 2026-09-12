
from collections import defaultdict
from booking_intent import cta_quality
from booking_partners import apply_booking_partner_attribution

_STATUS_ORDER = {"bookable":0,"useful":1,"weak":2,"missing":3}

def booking_coverage_report(events):
    apply_booking_partner_attribution(events)
    grouped=defaultdict(lambda:{"total":0,"bookable":0,"useful":0,"weak":0,"missing":0,"partners":defaultdict(int)})
    for e in events:
        names=getattr(e,"source_names",None) or ["Okänd källa"]
        q=cta_quality(e)
        for source in names:
            row=grouped[source]
            row["total"] += 1
            row[q["status"]] += 1
            partner=getattr(e,"booking_partner",None)
            if partner and q["status"]=="bookable":
                row["partners"][partner] += 1
    rows=[]
    for source,data in grouped.items():
        total=data["total"]
        bookable=data["bookable"]
        rows.append({
            "source":source,
            "total":total,
            "bookable":bookable,
            "booking_coverage": (bookable/total) if total else 0.0,
            "useful":data["useful"],
            "weak":data["weak"],
            "missing":data["missing"],
            "partners": dict(sorted(data["partners"].items(), key=lambda x:(-x[1],x[0]))),
        })
    rows.sort(key=lambda r:(-r["booking_coverage"],-r["bookable"],r["source"].casefold()))
    totals={"total":sum(r["total"] for r in rows),"bookable":sum(r["bookable"] for r in rows)}
    totals["booking_coverage"]=(totals["bookable"]/totals["total"]) if totals["total"] else 0.0
    return {"sources":rows,"totals":totals}
