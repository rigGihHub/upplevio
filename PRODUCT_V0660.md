# Upplevio v0.66.0 – Showtime Data Coverage

## Mål
Öka andelen event där `Pågår nu` kan avgöras från verifierad sluttid, utan att gissa varaktighet.

## Förändringar
- Ny konservativ detaljside-parser `showtime_enrichment.py`.
- Exakta klockintervall som `10.00–16.00` kan ge både start- och sluttid.
- Exakt slutmarkör som `23:00 – Slut` kan komplettera ett redan verifierat startklockslag.
- Parsern använder eventkontext och blockerar typiska öppettids-/kontaktsektioner.
- `booking_enrichment` återanvänder samma HTTP-hämtning för showtime-data och bokningslänk, så ingen extra detaljside-request behövs.
- Befintliga verifierade tider skrivs aldrig över.
- `ca 60 minuter`, `40–70 minuter` och `pågår till ca 12.55` används inte för att skapa ett skenbart exakt `end_time`.

## Produktprincip
Hellre okänd sluttid än en uppskattad sluttid. `Pågår nu` ska vara ett faktapåstående, inte en sannolikhetsbedömning.
