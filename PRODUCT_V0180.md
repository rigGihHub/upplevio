# Upplevio v0.18.0 — Lightweight Interest Personalisation

## Mål
Göra discovery-resultaten mer relevanta utan konto, auth eller svart-box-personalisering.

## Ändringar
- Valfri intresseprofil i huvudflödet.
- Intressen påverkar bara sorteringen; event utanför valda intressen filtreras inte bort.
- Regelbaserad och förklarbar intressematchning.
- Intressebonus är begränsad så explicit sökning, avstånd och tid fortsatt väger tungt.
- Eventkort kan förklara `matchar <intresse>` bland rankingorsakerna.
- Intresseval sparas endast i aktuell Streamlit-session via widget state; ingen användaridentitet införs.
- Sökfiltret använder samma accent-/diakritiknormalisering som rankingen, så `pokemon` kan matcha `Pokémon` även före rankingen.

## Medvetet inte byggt
- Konto/auth.
- Permanent profil i databas.
- ML/AI-personalisering.
- Hård filtrering på intressen.
- Matchprocent med falsk precision.
