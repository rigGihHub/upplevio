
# Upplevio v0.47.0 – Candidate Decision Engine

## Mål
Göra kandidatgranskningen beslutsbar över tid utan svart låda eller artificiell poäng.

## Implementerat
- varje kandidataudit sparar en snapshot per kandidat och dag
- samma dag uppdaterar dagens snapshot i stället för att skapa falska extra mätningar
- historik omfattar parserstatus, kandidatvolym, unik eventdata, överlapp, unik andel, bokningsbara event och eventtyper
- transparent beslut per kandidat:
  - Aktivera
  - Fortsätt mäta
  - Avstå
- varje beslut visar konkreta orsaker

## Aktiveringsregel
Aktivera kräver:
- minst 3 snapshots
- minst 3 olika dagar
- parserstabilitet minst 80 %
- återkommande unik nytta:
  - median minst 3 unika event, eller
  - median unik andel minst 35 %
- plus unik kategori, eller minst 5 unika event i median

## Avstå-regel
Avstå kan ske först efter minst 4 snapshots och kräver antingen:
- parserstabilitet högst 50 %, eller
- median unik andel högst 10 % och ingen unik eventtyp

Annars är beslutet Fortsätt mäta.

## Viktigt
Bokningsgrad är stödjande information men inget krav för aktivering. Kommunala, fria och lokala long-tail-event kan vara mycket värdefulla utan kommersiell bokningsväg.
