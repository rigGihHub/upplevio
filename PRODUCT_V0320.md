# Upplevio v0.32.0 — Local Long-tail Source Expansion

## Syfte
Öka faktisk lokal discovery-täckning utan att lägga till ännu en bred biljettkälla.

## Ny källa: City Örebro
- City Örebros publika evenemangskalender är aktiverad som lokal källa i Örebro.
- Importen accepterar bara eventkort med explicit titel och parsebart datum.
- Källans kategorietiketter används som tags när de faktiskt finns i listningen.
- Saknat pris förblir `unknown`; Upplevio antar aldrig gratis.
- Utgångna event filtreras bort.
- Källan körs som en oberoende SourceTask och kan därför fallera utan att slå ut övriga källor.

## Produktbedömning
Webbgranskning 2026-09-04 visade att City Örebros kalender innehåller flera typer av lokal long-tail som är strategiskt relevanta: familjeevent, konst, teater, sport, marknader och cityaktiviteter. Det gör källan mer intressant för Upplevios kärnlöfte än ännu en generell biljettkälla.

## Avgränsningar
- Ingen prisgissning.
- Ingen kopiering av långa beskrivningar.
- Ingen automatisk import av pressmeddelanden som event.
- Wadköping/Kulturkvarteret har identifierats som starka kandidater, men läggs inte in i samma release innan separat parser/överlappsvärde har bedömts.
- Livehämtning från Streamlit Cloud är inte verifierad före deploy.
