# Upplevio v0.59.0 – Culture Candidate Value

## Produktmål
Kandidatmotorerna ska inte belöna en källa bara för att den producerar fler poster. Upplevio ska mäta om källan faktiskt bidrar med upplevelser som saknas eller är tunt representerade i den befintliga discovery-importen.

## Ändringar
- Candidate Value Audit kopplas till Coverage Frontier.
- Varje kandidat redovisar vilka frontier-segment den över huvud taget representerar.
- Unika event redovisar vilka frontier-segment de tillför efter normal dedupe.
- Ny mätning: antal unika kandidat-event som ligger i segment som just nu är `Tunn` eller `Saknas i aktuell import`.
- Kandidat-snapshots lagrar frontier-värdet historiskt. Befintliga SQLite-filer migreras additivt med nya kolumner.
- Candidate Decision kan använda återkommande frontier-gap-value som stöd för aktivering; en enda snapshot räcker fortfarande aldrig.
- Admin visar frontier-värdet separat från parserträffar, unik andel och bokningsbarhet.

## Viktiga principer
- Ingen syntetisk totalscore införs.
- `Saknas i aktuell import` får inte beskrivas som ett marknadsgap.
- Överlappande event räknas inte som gap-fyllande bara för att de ligger i ett tunt segment.
- Kandidater påverkar fortfarande inte publik discovery före aktiveringsbeslut.
- Bokningsgrad är inte aktiveringskrav för fria/offentliga upplevelser.

## Nästa logiska steg
Community & Association Frontier bör övervägas först efter att kulturkandidaterna hunnit samla riktiga snapshots över flera dagar. Kandidatbeslut ska inte simuleras fram genom upprepade körningar samma dag.
