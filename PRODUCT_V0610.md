# Upplevio v0.61.0 – Outdoor & Nature Frontier

## Syfte
Bredda discovery mot natur, friluftsliv och utomhusupplevelser utan att förvandla platsinformation till påhittade event.

## Ändringar
- Karlslund är ny candidate-only källa via Örebro kommuns officiella Karlslund-sida.
- Parsern kräver explicit datum och accepterar inte allmän plats-/öppettidsinformation som event.
- Tid tas bara från explicit klockslag.
- Gratis sätts bara vid explicit Gratis/Fri entré/Ingen kostnad.
- Natur/outdoor-taggar sätts bara när källtexten faktiskt innehåller natur-, trädgårds-, park-, vandrings- eller skördesignal.
- Kandidaten går genom befintlig dedupe, frontier value, snapshots och Candidate Decision Engine.

## Källbeslut
- Oset/Rynningeviken och Naturens hus är viktiga discovery-områden men har i den aktuella granskningen främst plats-/aktivitetsinformation, inte en robust löpande publik eventkalender. De aktiveras därför inte som eventkälla i denna release.

## Trust
Ingen kandidat påverkar publik discovery före evidens över flera snapshots/dagar.
