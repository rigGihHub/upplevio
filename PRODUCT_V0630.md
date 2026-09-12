# Upplevio v0.63.0 – Source Quality Consolidation

## Mål
Sluta behandla alla kandidatparsers som lika värdefulla. Konsolidera historiken till en operativ arbetsprioritering utan att skapa en godtycklig totalscore eller kringgå Candidate Decision Engine.

## Nytt
- Ny modul `candidate_portfolio.py`.
- Kandidatkällor grupperas i `Aktiveringskandidat`, `Prioritera mätning`, `Parserproblem`, `Fortsätt mäta` eller `Låg prioritet`.
- Portföljvyn använder bara observerad historik: parserstabilitet, antal observationsdagar, median unika event, median unik andel, unika event i tunn/saknad Coverage Frontier och andel lyckade snapshots med noll unik nytta.
- En enda stark körning kan aldrig höja en kandidat till prioriterad mätning.
- Upprepade parserfel eller minst fyra dagars stabil men i praktiken noll unik nytta synliggörs som underhålls-/prioriteringsproblem.
- Candidate Decision Engine är fortfarande ensam auktoritet för `Aktivera`, `Fortsätt mäta` och `Avstå`.
- Ingen viktad totalscore införs.

## Produktprincip
Källor kostar underhåll. En källa som inte återkommande förbättrar discovery ska inte behållas av sentiment eller för att den en gång byggdes. Samtidigt ska källor inte avfärdas på en enda dålig dag.

## Version
`APP_VERSION = "0.63.0"`
