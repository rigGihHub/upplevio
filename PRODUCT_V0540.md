
# Upplevio v0.54.0 – Last Minute

## Mål
Göra event som faktiskt går att agera på inom de närmaste timmarna extremt lätta att hitta.

## Implementerat
- nytt Nightline-val: Last Minute
- endast event med känd starttid kvalificerar
- tidsfönster: 30–180 minuter från aktuell svensk tid
- starttider utanför fönstret eller saknad starttid kvalificerar inte
- upp till tre högst rankade Last Minute-event lyfts först
- ordningen följer befintlig organisk discovery-ranking
- snabbfakta visar:
  - tid kvar till start
  - avstånd från vald stad när känt
  - pris/prisstatus
  - om en faktisk boknings-CTA finns
- övriga kvalificerade event visas under "Fler som börjar snart"
- Last Minute har egen engagement-surface: `last_minute`

## Dataprincip
Upplevio gissar aldrig starttid. Saknad eller ogiltig starttid betyder att eventet inte kan visas i Last Minute.
