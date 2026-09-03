# Upplevio v0.12.0 — Geographic Discovery Reliability

Mål: relevanta event ska inte försvinna enbart för att en källa saknar eventets lat/lon, utan att Upplevio hittar på exakta avstånd.

## Ändrat
- Konservativ ortsnormalisering för kända orter, inklusive diakritik och tydliga suffix som `kommun`/`stad`.
- Geografisk fallback i ordningen: eventkoordinat → venue-koordinat → kuraterad stadspunkt → okänd.
- Geo-confidence: `exact`, `venue`, `city`, `unknown`.
- Stadspunktsavstånd visas som ungefärligt (`ca X km`) i eventkort.
- Okända orter får aldrig fabricerat avstånd och räknas inte som inom vald radie.
- Fler relevanta svenska orter i den kuraterade ortstabellen, särskilt runt Örebro.
- Fokuserade tester för exakta koordinater, venue-fallback, Örebro-normalisering, Stockholm kontra 100 km och okänd ort.

## Medveten begränsning
Detta är inte geokodning. Upplevio gissar inte koordinater från fri adress eller okända ortsnamn. Sådan funktion kräver senare en separat, verifierad geokodningskälla.
