# Upplevio v0.76.0 – Parser Regression Guardrail Registry

## Syfte
Göra parserregressioner synliga direkt genom ett gemensamt, deterministiskt register med positiva och negativa historiska parserfall per källa och fält.

## Ändrat
- Ny modul `parser_guardrails.py`.
- Nätverksfritt guardrail-register baserat på minimala verklighetsnära HTML-fixtures.
- Skyddar starttid, sluttid, pris, dörrtid, åldersgräns, venue och bokningslänk.
- Innehåller både positiva fall och negativa säkerhetsfall.
- Conventum-format från evidensarbetet skyddas, inklusive `20:00 – start`, explicita tidsintervall och `Entré 120 kr`.
- Ungefärlig sluttid, service-/garderobsavgift, sociala bokningslänkar, javascript-URL och okända externa bokningshosts förblir blockerade.
- Admin visar total guardrail-status och exakt vilket fall som eventuellt har brutits.
- Guardrails körs i ordinarie pytest-svit.

## Princip
Registret är inte live-webbtestning. Källsidor förändras och kan ligga nere. Guardrails skyddar i stället det parserbeteende som Upplevio redan har verifierat och beslutat ska gälla.

## Tester
344 tester passerar.
