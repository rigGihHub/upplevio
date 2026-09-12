# v0.74.0 – Evidence-backed Parser Fixes

Den första faktiska parserfix-releasen byggd ovanpå Gap → Fix → Evidence → Batch → Recommendation-kedjan.

## Genomfört

- `showtime_enrichment.extract_explicit_showtime` kan nu läsa explicit märkta start-rader som `20:00 – start`.
- En befintlig verifierad starttid skrivs aldrig över av en motstridig start-markör.
- Ungefärliga sluttider som `ca 22:30 – slut` lämnas fortsatt tomma.
- `booking_enrichment.extract_detail_facts` accepterar nu explicit entrépris i formatet `Entré 120 kr`.
- Serviceavgift, garderobsavgift och andra lösa belopp blir fortsatt inte eventpris.
- Positiva och negativa regressionstester har lagts till för båda fixarna.

## Princip

Bara mönster med tydlig, verifierbar semantik har breddats. Ingen generell fuzzy matchning eller varaktighetsaritmetik har lagts till.
