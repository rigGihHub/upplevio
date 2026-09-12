
# Upplevio v0.38.0 – Direct Booking Link Enrichment

- Officiella eventdetaljsidor kan nu enrichas med faktisk boknings-/biljettlänk.
- Första aktiverade källan är Conventum, där eventlistan redan ger individuella detaljsidor.
- Endast tydliga CTA-ankare som Boka/Köp biljett/Biljetter accepteras.
- Ingen bokningslänk gissas från vanlig text eller allmän startsida.
- Enrichment kör parallellt, är begränsad till 12 event per import och får aldrig fälla grundimporten.
- booking_partner sparas från destinationsdomänen.
- Visit Örebros redaktionella samlingssidor enrichas inte automatiskt eftersom de saknar säker 1:1-koppling till varje arrangörs detaljsida.
