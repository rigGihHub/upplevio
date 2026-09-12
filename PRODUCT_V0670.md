# Upplevio v0.67.0 – Event Detail Intelligence

## Syfte
Använd redan hämtade officiella eventdetaljsidor bättre utan att gissa eller öka brus i discovery-ytan.

## Nytt
- `Event` har frivilliga `door_time` och `age_limit`.
- Detalj-enrichment kan hämta uttrycklig dörr-/insläppstid och uttryckligt märkt åldersgräns.
- Generiska `Conventum` kan förfinas till `Conventum Kongress`, `Conventum Arena` eller `Hjalmar Bergman Teatern` när detaljsidan uttryckligen anger detta.
- Pris kompletteras bara från uttryckligt märkta biljett-/entréprisrader. Garderobsavgifter eller andra belopp får inte bli eventpris.
- Event som redan har bokningslänk kan fortfarande få praktisk detaljinformation.
- Publika kort hålls kompakta; praktisk info visas först under `Detaljer`.

## Trust-regler
- Ingen dörrtid räknas ut från “en timme innan”.
- Ingen åldersgräns infereras från eventtyp eller servering.
- Inget omärkt belopp används som eventpris.
- Befintliga verifierade värden skrivs inte över.
