# Upplevio v0.23.0 — Event Card Scanability & Mobile Hierarchy

## Mål
Göra resultatlistan snabbare att läsa på mobil och ta bort visuell/repetitiv friktion utan att lägga till nya funktioner.

## Förändringar
- Ny eventkortshierarki: eventtyp → titel → datum/tid → plats/avstånd → pris → källstatus.
- Relativa svenska datum i kort: Idag, Imorgon, annars kort veckodag + datum.
- Starttid visas när den finns; sekunder kapas bort i discovery-vyn.
- Avstånd märks `ca` när det bygger på ortscentrum, annars exaktare km-format.
- NY, GRATIS och statusvarningar ligger som små sekundära badges.
- Samma event visas inte längre i både “Nytt”, “Gratis” och “Bäst match först”. Ett event visas en gång i huvudresultatet; badges och befintliga filter räcker.
- “Detaljer” öppnas inline direkt under rätt kort i stället för som en separat sektion efter hela resultatlistan.
- Sparade event får samma inline-detaljer och en tydlig “Ta bort sparad”-knapp.
- Mobil CSS komprimerad för bättre läsbarhet och mindre kort-höjd.

## Produktprincip
Förstavy ska besvara: Vad? När? Var? Hur långt? Vad kostar det? Allt annat är sekundärt.

## Verifiering
- 67/67 pytest-tester passerar.
- `python -m compileall -q .` passerar.
- Live Streamlit/mobilbrowser är inte verifierad förrän releasen pushas/deployas.
