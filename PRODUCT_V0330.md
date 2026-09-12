# Upplevio v0.33.0 – Source Overlap & Unique Value

## Mål

Mäta om en datakälla faktiskt tillför event som Upplevio annars inte hade haft, innan fler lokala källor integreras.

## Ny diagnostik

Admin har nu **Källornas unika värde · 30 dagar**.

För varje källa visas:

- event där källan finns representerad efter deduplicering
- unika event: event som bara har den källan
- överlapp: event som bekräftats/slagits ihop med minst en annan källa
- unik andel
- försiktig signal: högt unikt tillskott, blandat tillskott, stor överlappning eller för litet underlag

Dessutom visas parvis källöverlappning, exempelvis hur många sammanslagna event City Örebro och Visit Örebro delar.

## Viktig begränsning

Detta är inte en långsiktig ROI-poäng och inte ett mått på hela marknaden. En 30-dagarsperiod kan vara säsongsberoende. Tveksamma dublettkandidater räknas inte som överlapp eftersom Upplevio inte har tillräcklig säkerhet för att slå ihop dem.

Ingen källa bör tas bort enbart på en enstaka snapshot.

## Produktbeslut

Nästa lokala källa ska inte läggas till bara för att den innehåller många event. Värdet ska bedömas mot hur många nya relevanta event den faktiskt tillför jämfört med befintlig import.
