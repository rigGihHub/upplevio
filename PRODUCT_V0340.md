# Upplevio v0.34.0 – Discovery Quality Guardrails

## Mål
Skydda kärnupplevelsen när datatäckningen växer. Mer eventdata är bara värdefullt om toppresultaten fortfarande är lätta att skanna och relevanta.

## Infört
- Ny `discovery_quality.py` för konservativ diagnostik av synliga toppresultat.
- Admin analyserar standardupplevelsen: Örebro, nästa 7 dagar, 50 km, alla priser.
- Flaggar möjliga nästan-dubletter med samma datum och mycket lik titel.
- Flaggar svaga/generella titlar.
- Synliggör käll- och eventtypskoncentration i topp 10.
- Flaggar centrala metadatafel utan att göra saknad starttid till ett generellt kvalitetsfel.
- Ingen av signalerna filtrerar bort event automatiskt.

## Produktprincip
Long-tail-källor har ofta tunnare metadata än stora biljettkällor. Guardrails får därför inte skapa ett systematiskt bias mot små lokala arrangörer. Diagnostiken ska hjälpa oss hitta brus och parserproblem, inte belöna stora källor för att de har rikare metadata.

## Avgränsning
Ingen sammansatt kvalitetsprocent eller artificiellt betyg införs. Ingen automatisk suppression av event införs i denna release.
