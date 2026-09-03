# Upplevio v0.17.0 — Explainable Discovery Ranking

## Mål
Göra huvudresultatet bättre på kärnuppgiften: visa de mest användbara eventen först utifrån användarens faktiska val, utan svart-box-AI eller falsk precision.

## Förändringar
- Ny regelbaserad `discovery_rank()` i `discovery.py`.
- Huvudresultaten sorteras nu på en kombination av:
  - explicit sökrelevans,
  - avstånd,
  - hur snart eventet händer,
  - pris/budget,
  - källförtroende som liten tie-breaker.
- Källförtroende är avsiktligt lågt viktat och får inte göra ett ointressant event relevant.
- Saknat pris ger ingen prisbonus och tolkas aldrig som gratis/billigt.
- Saknade geodata ger ingen avståndsbonus.
- Söktext normaliseras accent-/diakritikoberoende, t.ex. `pokemon` matchar `Pokémon`.
- Eventkort i huvudresultatet visar upp till tre korta skäl, t.ex. `mycket nära · händer snart · gratis`.
- Rubriken `Alla resultat` ersätts av `Bäst match först`.
- Ingen procentuell "AI-match" används; poängen är intern och presentationen förklarar skälen i ord.

## Tester
Fem nya fokuserade rankingtester täcker:
- nära/snart mot långt/senare,
- titelträff mot svagare beskrivningsträff,
- okänt pris får ingen värdebonus,
- källförtroende får inte dominera relevans,
- korta/förklarbara rankningsskäl.

Hela testsamlingen: 39/39 passerar.
`python -m compileall -q .` passerar.

## Inte verifierat
- Publicerad Streamlit-app i webbläsare.
- Mobil rendering.
- Livebeteende med riktiga externa API-anrop.
