# Upplevio v0.79.1 — Alternate Date Detail Guardrail

## Mål

Säkerställa att discovery-kollapsen inte döljer vilka andra föreställningsdatum som finns.

## Förändringar

- `+N DATUM` behålls som kompakt kortbadge.
- Detaljpanelen visar de alternativa datumen i kronologisk ordning.
- Presentationen behåller referenser till de alternativa eventen utan att ändra ordinarie eventdata-dedupe.
- Regressionstest verifierar att samtliga alternativa event och datum bevaras.

## Releasevillkor

Kandidaten ska fortfarande visuellt verifieras i riktig desktop- och mobilrendering innan commit/push.
