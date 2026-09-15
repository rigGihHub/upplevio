# Upplevio v0.80.0

Latest release: Calm Discovery UI. See PRODUCT_V0800.md.

# Upplevio v0.78.0

Latest release: Discovery Layout & Production Collapse. See PRODUCT_V0780.md.

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

## v0.28.0 — Coverage Gap Intelligence

Benchmarken har utökats från ren träffprocent till diagnostik per kategori, venue och referenskälla. Admin visar nu var benchmark-luckorna faktiskt finns, så nästa källintegration kan prioriteras efter observerad täckningsvinst i stället för magkänsla. Benchmarken är fortfarande endast en manuellt kuraterad sample och får inte beskrivas som marknadstäckning.

## v0.29.0 — Benchmark Quality & Long-tail Blind Spots

Benchmark-Admin analyserar nu även kvaliteten på själva referensmängden. Den visar representerade discovery-segment, blindfläckar och varningar för liten eller dominerad sample. Ingen artificiell kvalitetsprocent används och inga nya referensevent läggs till utan verifiering.

## v0.30.0 — Verified Benchmark Expansion

Benchmarken har utökats med sju verifierade referensevent från Örebro Teater och Visit Örebro inom den befintliga benchmarkperioden. Scen & teater, familj och sport får därmed bättre representation. Admin visar nu senaste verifieringsdatum och antal referenskällor dynamiskt. Inga syntetiska event har lagts till för att fylla kvarvarande blindfläckar.


## v0.32.0 — Local Long-tail Source Expansion
City Örebro är nu en default-aktiverad lokal discovery-källa med konservativ titel/datum-import, failure isolation och utan prisgissningar.

## v0.33.0

Source Overlap & Unique Value: Admin mäter nu unika event per källa, överlapp och parvisa källöverlappningar för aktuell 30-dagarsperiod. Diagnostiken är avsiktligt en snapshot och används inte som falsk långsiktig ROI-poäng.

## v0.34.0 — Discovery Quality Guardrails

Admin granskar nu Upplevios standardiserade topp 10-resultat för möjliga nästan-dubletter, svaga/generella titlar, centrala metadatafel samt koncentration till en enda källa eller eventtyp. Signalerna är diagnostik och filtrerar inte automatiskt bort long-tail-event.

## v0.36.0
Result Trust & Noise Suppression: konservativ automatisk suppression av tydliga parserartefakter, separat review-signal för osäkra fall och Admin-diagnostik per källa. Legitima long-tail-event med tunn metadata ligger kvar.


## v0.36.0 – Booking & Revenue Foundation
Se `PRODUCT_V0360.md`. Kommersiell grund är förberedd men annonser och sponsrade placeringar är inte aktiverade.


## v0.37.0 – Booking Intent & CTA Quality
Se `PRODUCT_V0370.md`. CTA-ordval och bokningsmätning är nu konservativt klassade; ingen extern informationslänk får automatiskt kallas bokning.


## v0.38.0 – Direct Booking Link Enrichment
Se `PRODUCT_V0380.md`. Första källan med försiktig detaljside-enrichment är Conventum.


## v0.39.0 – Booking Coverage Expansion
Se `PRODUCT_V0390.md`. City Örebro får säker detaljside-enrichment och Admin mäter verifierad bokningstäckning per källa.


## v0.40.0 – Booking Partner Attribution
Se `PRODUCT_V0400.md`. Bokningsplattform och affiliate-status hålls nu strikt separerade.


## v0.41.0 – Conversion Attribution Foundation
Se `PRODUCT_V0410.md`. Click-id och partnerkonverteringar kan nu kopplas samman utan att påstå att någon extern partnerintegration är live.


## v0.42.0 – Tracked Booking Redirect
Se `PRODUCT_V0420.md`. Signerad, idempotent redirectspårning med fail-safe direktlänk när konfiguration saknas.


## v0.43.0 – Booking Funnel Intelligence
Se `PRODUCT_V0430.md`. Visning, faktisk detaljöppning och bokningsutklick mäts nu som separata funnelsteg.


## v0.44.0 – Örebro Source Expansion
Se `PRODUCT_V0440.md`. Örebro Konserthus och Örebro Teater är nya officiella lokala förstahandskällor.


## v0.45.0 – Local Source Value Audit
Se `PRODUCT_V0450.md`. Lokala källor jämförs nu på unik eventdata, överlapp, kategoribidrag och bokningstäckning utan konstgjord totalscore.


## v0.46.0 – Kulturkvarteret & Wadköping Candidate Audit
Se `PRODUCT_V0460.md`. Kandidatkällor simuleras mot liveimporten utan att påverka publik discovery.


## v0.47.0 – Candidate Decision Engine
Se `PRODUCT_V0470.md`. Kandidatkällor får nu transparent beslut över flera snapshots: Aktivera, Fortsätt mäta eller Avstå.


## v0.48.0 – Future Carnival Identity
Se `PRODUCT_V0480.md`. Upplevio har nu en futuristisk festival-/cirkusidentitet med mörk nattbas, neon, portal-hero och biljettliknande eventkort.


## v0.49.0 – Event Poster Cards
Se `PRODUCT_V0490.md`. Eventkort har nu egna futuristiska poster-teman per eventtyp.


## v0.50.0 – Festival Map Feel
Se `PRODUCT_V0500.md`. Discovery har nu visuella festivalzoner utan faktisk kartfunktion.


## v0.51.0 – Nightline Navigation
Se `PRODUCT_V0510.md`. Discovery har nu snabba Nightline-val för tid, pris, närhet, Hidden Gems och familj.


## v0.52.0 – Showtimes
Se `PRODUCT_V0520.md`. Eventkort visar nu säkra tidsstatusar och Nightline-valet Ikväll använder känd starttid.


## v0.53.0 – Tonight Mode
Se `PRODUCT_V0530.md`. Ikväll-läget visar nu de tre högst rankade kvällseventen först, med snabb beslutsinformation och samma organiska ranking.


## v0.54.0 – Last Minute
Se `PRODUCT_V0540.md`. Nightline kan nu lyfta event med säker starttid 30–180 minuter framåt, utan separat rankingmotor.


## v0.55.0 – Go Now
Se `PRODUCT_V0550.md`. Nightline kan nu lyfta event med konservativ planeringsmarginal utifrån känd starttid och avstånd från vald stad, utan restidslöfte eller separat ranking.

## v0.56.0 – Örebro Coverage Frontier
Se `PRODUCT_V0560.md`. Admin visar nu 16 eventsegment över 30/60/90 dagar med källdiversitet och enkällsberoende. Visit Örebro-mismatchen i lokal källaudit är korrigerad.


## v0.57.0 – Örebro universitet Candidate Source
Se `PRODUCT_V0570.md`. Örebro universitet mäts nu som strikt kandidatkälla för lokala event som uttryckligen är öppna för alla.


## v0.61.0 – Outdoor & Nature Frontier
Karlslund candidate-only med konservativ eventparser; Oset/Naturens hus hålls utanför tills robust eventfeed finns.


## v0.63.0 – Source Quality Consolidation
Ny kandidatportfölj för arbetsprioritering utifrån observerad unik nytta, Coverage Frontier och parserstabilitet. Ingen totalscore; Candidate Decision Engine är fortsatt aktiveringsauktoritet.


## v0.64.0 – Booking Link Safety Hardening

Strict validation of inferred booking links: only HTTP(S), official-host links with strong CTA, or known ticket partners are accepted. Social links, unsafe schemes, generic homepages, fragments and unknown external hosts are rejected. Generic “Biljetter” requires stronger target evidence, and broad English “book” matching has been removed.

## v0.65.0 – Showtime End Time Foundation
`end_time` är nu ett riktigt frivilligt modellfält. UI och showtime-logik använder verifierad sluttid utan att gissa varaktighet.

## v0.66.0 – Showtime Data Coverage
Se `PRODUCT_V0660.md`. Eventdetaljsidor kan nu komplettera exakta start-/sluttider från uttryckliga klockintervall eller slutmarkörer. Ungefärlig längd används aldrig för att räkna fram sluttid.

## v0.73.0 – Parser Fix Recommendation
Admin kan nu översätta en återkommande batch-evidens till ett konkret, read-only parserförslag med målmodul, målfunktion, evidensexempel och obligatoriska regressionstester. Ingen kod ändras automatiskt.

## v0.74.0 – Evidence-backed Parser Fixes

Första evidensstödda parserfixarna: explicit `HH:MM – start` och explicit `Entré N kr`, med negativa regressionstester för ungefärlig sluttid, serviceavgift och motstridig verifierad starttid.

## v0.75.0 – Parser Fix Impact Audit
Replay-baserad före/efter-audit för v0.74-fixarna. Jämför samma HTML mot pre-v0.74 och aktuell parser, visar återvunna värden och regressioner utan att påstå live-effekt före deploy.


## v0.78.0 — Discovery Layout & Production Collapse
Tvåkolumnslayout på desktop, kompaktare actions och discovery-only kollaps av upprepade föreställningar utan att slå ihop de underliggande eventdata-posterna.
