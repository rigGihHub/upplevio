# Upplevio v0.69.0 — Detail Gap Prioritizer

## Syfte
Göra detaljauditen handlingsbar: peka ut vilken källa + vilket detaljfält som bör förbättras härnäst.

## Förändringar
- Ny transparent `detail_gap_priorities()` utan dold totalscore.
- Prioriterar först återkommande luckor i enkällsevent, eftersom attributionen där är renare.
- Stora luckor i fler-källevent kan fortfarande få hög prioritet, men märks uttryckligen som svagare provenienssignal.
- Små stickprov markeras `För lite data` och får inte driva parserarbete.
- Admin visar källa, fält, täckning, antal saknade event, antal saknade enkällsevent och begriplig motivering.
- Detaljauditen lagrar nu även fälttäckning för enkällsevent som underlag för prioriteringen.

## Princip
Prioriteringen är en arbetskö, inte ett påstående om marknadstäckning eller exakt fältproveniens för deduplicerade fler-källevent.
