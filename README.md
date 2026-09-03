# Upplevio v0.11.0

**Upptäck mer. Upplev mer.**

Den här versionen prioriterar datatäckning och prestandasäker import före nya funktioner.

## Viktigast i v0.11.0

- Paginerad Ticketmaster-import.
- Paginerad Visit Sweden-import med konservativ säkerhetsgräns.
- 15 minuters cache för extern eventdata i Streamlit.
- Intern täckningsdiagnostik utan falska påståenden om procentuell marknadstäckning.
- Produktionssäkert demoläge från v0.9.0 kvarstår.

## Ticketmaster

Lägg `TICKETMASTER_API_KEY` i Streamlit secrets eller som miljövariabel.

## Demo

Fiktiv testdata är avstängd som standard. För lokal UX-testning kan `UPPLEVIO_DEMO_MODE=true` sättas explicit.

## Lokal start

```bash
pip install -r requirements.txt
streamlit run app.py
```


## v0.11.0
Huvudflödet är förenklat till Var → När → Hur långt → Budget. Prisdata från Ticketmaster stöds, tekniska källval är undanplockade och okänt pris behandlas aldrig som gratis.


## v0.14.0
Lokal officiell pilotkälla: Conventums arrangemangskalender i Örebro, plus benchmarkdiagnostik per referenskälla.


## v0.15.0
Visit Örebro är tillagd som kompletterande officiell lokal discovery-källa via aktuella redaktionella eventlistor. Importen tar endast strukturerade fakta (datum, titel, plats och uttryckligt gratis-status), kopierar inte artikelbeskrivningar eller bilder och länkar tillbaka till källsidan. Den klientrenderade huvudkalendern används inte eftersom dess underliggande feed/API inte har verifierats.


## v0.18.0 – Lightweight Interest Personalisation
- Valfri intresseprofil utan konto.
- Intressen förbättrar rankingen men filtrerar inte bort andra event.
- Förklarbar intressebonus i discovery.
- Accentnormaliserat sökfilter (`pokemon` matchar `Pokémon`).

## v0.17.0
Multi-source merge och tydligare källförtroende. Samma event från flera oberoende källor kan slås ihop konservativt med bevarad proveniens. Eventkort skiljer på källverifierat och bekräftat från flera källor.


## v0.17.0 – Explainable Discovery Ranking
Huvudresultaten använder nu en transparent regelbaserad ranking baserad på sökrelevans, avstånd, tid och pris. Källförtroende används endast som liten tie-breaker. Eventkort förklarar kort varför ett event rankas högt.
