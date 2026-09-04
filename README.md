# Upplevio

Senaste release: **v0.25.0 – Top-result Ranking Quality**

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

## v0.22.0
Källhälsa och tyst felupptäckt: konservativ diagnostik för tomma aktiva källor, importfel och sannolika parserregressioner. Säsongstomma källor behandlas separat. Rå exceptiontext exponeras inte längre i Admin.


## v0.22.0

- Smart nollträffs-fallback med tydligt märkta nära alternativ.
- Breddar ett filter i taget och ändrar aldrig användarens aktiva val i bakgrunden.
- Sökord och eventtyp relaxeras inte automatiskt.
- Kan som sista steg föreslå kombinerad längre period + större radie när en enda lättnad inte räcker.


## v0.23.0
Förbättrad eventkortshierarki och mobil scanability: varje event visas en gång, snabbfakta prioriteras och detaljer öppnas inline under rätt kort.


## v0.24.0
Första 10 sekunderna är förenklade: tydligare kärnlöfte, två rader med Var → När → Hur långt → Budget, snävare relevanta standardval och alla sekundära val samlade under “Fler val”.


## v0.25.0

- Förbättrad ranking av de första 10 resultaten utan ny tung rekommendationsmodell.
- Nästan likvärdiga event kan spridas ut efter eventtyp, arena och datum så att toppen inte domineras av samma sorts event.
- Diversifiering får endast påverka kandidater inom ett smalt poängband; tydligt högre relevans, närhet, tid eller explicit sökträff skyddas.
- Grundpoäng och förklaringar ändras inte av diversifieringen.
- Deterministisk tie-break: grundscore, datum och titel; ingen slumpmässig ordning.
- 73 tester passerar i releasebygget.


## v0.26.0 — Result Density & Performance
- Renderar bara aktiv huvudvy i stället för alla Streamlit-tabs vid varje rerun.
- Visar 12 resultat åt gången med "Visa fler".
- Cachear dedupe och källhälsa på oförändrad import.
- Undviker upprepade SQLite-skrivningar av event sightings vid rena UI-reruns.
- 78 tester passerar.

## v0.27.0 — Source Latency & Failure Isolation

Oberoende datakällor hämtas parallellt och ett källfel isoleras utan att kasta bort lyckade källors resultat. Diagnostikordningen är fortsatt deterministisk. Liveprestanda är inte verifierad före deploy.
