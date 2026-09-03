# Upplevio v0.13.0 — Örebro benchmark coverage

## Mål
Göra datatäckning mätbar mot en explicit, oberoende referensmängd i stället för att dra slutsatser från Upplevios egna importerade data.

## Nytt
- `benchmark.py` med konservativ matchning på datum + ort + titellikhet.
- Ett Upplevio-event får maximalt täcka en benchmarkrad.
- Daterad referensfil: `data/benchmark_orebro_2026-09.csv`.
- Referensen innehåller 25 manuellt kuraterade, verkliga event i Örebro 4 september–3 oktober 2026.
- Källor för referensen: Visit Örebro och Conventums officiella kalendrar, kontrollerade 2026-09-03.
- Admin visar antal referensevent, hittade event, benchmark-täckning och exakt vilka referensevent som saknas.

## Viktig begränsning
Benchmark-procenten är **inte** andelen av alla verkliga event i Örebro. Den gäller endast den explicit dokumenterade referensmängden. Referensen behöver byggas ut med fler oberoende källor och kategorier innan den kan användas som bred kvalitetsindikator.

## Varför detta prioriterades
Upplevios kärnproblem är datatäckning. Utan en extern referensmängd går det inte att veta om fler importer faktiskt gör discovery bättre eller bara ökar antalet poster.
