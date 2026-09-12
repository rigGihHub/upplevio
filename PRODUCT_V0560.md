# Upplevio v0.56.0 – Örebro Coverage Frontier

## Mål
Återföra utvecklingen till Upplevios högsta prioritet: datatäckning. Releasen visar vilka typer av upplevelser som är bra representerade, tunna eller helt saknas i den aktuella importen.

## Frontier-segment
16 konkreta segment: stora konserter, lokal livemusik, teater/scenkonst, stand-up/humor, museum/utställning, familj/barn, publiksport, marknad/mässa, mat/dryck, samtal/föreläsning, workshop/deltagande, nattliv/klubb, natur/utomhus, säsong/högtid, förening/lokalsamhälle samt student/universitet.

## Rapport
För varje segment visas 30/60/90-dagars närvaro, källdiversitet, antal betrodda källor och enkällsberoende. Status är endast `Bra täckning`, `Tunn` eller `Saknas i aktuell import`. Frånvaro beskrivs aldrig som ett bevisat marknadsgap.

## Källresearch 2026-09-07
- Örebro universitets officiella kalendarium är en stark kandidat. Det innehåller aktuella poster med datum, tid och plats och kan filtreras till evenemang öppna för alla. Det kan stärka student/universitet, föreläsningar, öppna hus, kultur och forskning.
- Örebro läns museum har en officiell kalender med aktuella aktiviteter trots att huvudbyggnaden är stängd för renovering till 2027. Kandidaten bör därför mätas som en distribuerad kultur-/historiekälla, inte som enbart museibyggnaden.
- OpenArt har en officiell evenemangskalender för 2026 och är relevant för konst, workshops och familjeaktiviteter, men är säsongsbetonad och bör inte ensam användas som permanent täckningssignal.
- Naturens hus/Naturskolan har relevanta naturaktiviteter, men hittad publicering är mer fragmenterad. Fortsatt kandidatgranskning före parser.

## Korrigeringar
- Lokal källaudit känner nu igen både `Visit Örebro` (faktiskt importerad source_name) och registry-namnet `Visit Örebro – redaktionella eventlistor`.
- Kolumnen `Unika eventtyper` har förtydligats till `Eventtyper bland egna unika event`.
- `event_visual_theme` hanterar nu även tags som råkar vara en sträng utan att splitta den i enskilda tecken.

## Nästa rekommendation
Bygg kandidatparser för Örebro universitet först och mät faktisk unik nytta mot nuvarande import innan källan default-aktiveras.
