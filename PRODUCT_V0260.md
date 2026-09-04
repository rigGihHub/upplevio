# Upplevio v0.26.0 — Result Density & Performance

## Mål
Göra vanliga interaktioner i Streamlit snabbare utan att minska datakvalitet eller gömma användarkontroll.

## Förändringar

### 1. Endast aktiv huvudvy renderas
Tidigare användes `st.tabs`, vilket innebär att innehållet i Upptäck, Sparat och Admin exekveras vid samma rerun. v0.26.0 använder en horisontell vyväljare och renderar endast den aktiva vyn.

Effekt: benchmark, källstatus, dataramar och dublettdiagnostik körs inte när användaren bara söker eller sparar event.

### 2. Resultat renderas i batcher
Huvudlistan visar initialt 12 event. Användaren kan därefter visa 12 till åt gången. När ett filter ändras återställs visningen till första batchen.

Detta minskar antalet eventkort, expanders och knappar som Streamlit måste bygga om på varje rerun.

### 3. Deduplicering och källhälsa cacheas
Den redan cacheade råimporten kompletteras med cache för deduplicering och aktuell källhälsobedömning. UI-reruns behöver därför inte upprepa dessa beräkningar så länge den importerade datan är oförändrad.

### 4. Event sightings skrivs inte om på varje UI-rerun
`event_seen.last_seen_at` uppdaterades tidigare varje gång Streamlit körde om scriptet. Nu skapas en stabil signatur av den importerade eventmängden och skrivning sker endast när eventmängden ändras i sessionen.

Detta minskar SQLite-skrivningar och ligger bättre i linje med att sightings beskriver ingestion, inte knapptryckningar.

## Avsiktliga begränsningar
- Ingen påstådd millisekundsvinst utan browserprofilering i deployad miljö.
- Ingen migration från Streamlit.
- Ingen aggressiv parallellisering eller förtida optimering av dedupe-algoritmen.
- Detaljer renderas fortfarande för de synliga korten; batchningen begränsar kostnaden.

## QA
- 78/78 tester passerar.
- `python -m compileall -q .` passerar.
- Release-ZIP kontrolleras separat för integritet och oönskade lokala filer.
