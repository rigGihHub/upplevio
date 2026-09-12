# Upplevio v0.58.0 – Culture & Exhibition Frontier

## Mål
Öka datatäckningen för museum, konst, utställningar och mindre kulturarrangemang utan att sänka trust-nivån eller slå på oprövade källor publikt.

## Implementerat
- Örebro läns museums officiella kalender är tillagd som **candidate-only** källa.
- Parsern kräver explicit datum och skapar aldrig starttid när sådan saknas.
- Ort lämnas medvetet tom när kalenderkortet inte verifierar Örebro stad; regionen anges som Örebro län.
- Kalenderns kultur-taggar bevaras konservativt för bättre frontier-klassificering.
- Candidate Value Audit visar nu vilka Coverage Frontier-segment varje kandidat faktiskt kan bidra till.
- Källan går genom befintligt flöde: fetch → parse → dedupe → unique value → snapshot → candidate decision.
- Ingen ny kulturkälla aktiveras i publik discovery i denna release.

## Källbeslut
Örebro läns museum är en stark kandidat eftersom den officiella kalendern innehåller visningar, föreläsningar, hantverk och utställningsrelaterade aktiviteter som passar Upplevios long-tail-löfte. Museibyggnaden i Örebro är samtidigt stängd för renovering och kalendern innehåller aktiviteter runt länet. Därför vore det fel att hårdkoda alla poster som Örebro stad.

OpenArt 2026 avslutades 6 september 2026. OpenArt läggs därför inte in som ny löpande kandidat i v0.58.0 enbart för att fylla en kategori; den bör bedömas igen inför nästa aktiva biennal/programperiod.

## Guardrail
Candidate-only betyder fortsatt att en lyckad hämtning inte är ett aktiveringsbeslut. Candidate Decision Engine behöver flera dagsobservationer och återkommande unik nytta.
