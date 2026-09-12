# Upplevio v0.46.0 – Kulturkvarteret & Wadköping Candidate Audit

## Mål
Bevisa kandidatnytta innan fler lokala källor påverkar publik discovery.

## Implementerat
- Kulturkvarteret och Wadköping som kandidatkällor, inte aktiva discovery-källor
- kandidater hämtas endast från Admin när användaren väljer att köra audit
- konservativ SiteVision-parser kräver titel + explicit svenskt datum/datumintervall
- datumintervall blir ett event, inte ett event per dag
- kandidat-detailpages kan berikas med befintlig explicit booking-CTA-logik
- simulering kör Upplevios vanliga dedupe på kopior av liveevents + kandidater
- audit visar parserträffar, event efter dedupe, unika event, överlapp, unik andel, bokningsbara event och eventtyper
- live-eventlistan muteras inte av audit
- kandidatfel isoleras per källa

## Beslutsregel
Ingen kandidat default-aktiveras i denna release. Aktivering ska baseras på faktisk unik eventdata/kategorinytta över flera snapshots, inte bara hög rå eventvolym.
