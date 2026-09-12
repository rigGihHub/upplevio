# Upplevio v0.29.0 — Benchmark Quality & Long-tail Blind Spots

## Varför

Coverage Gap Intelligence i v0.28.0 gjorde benchmarken bättre på att visa vad Upplevio missar. Men själva benchmarken är fortfarande liten och kraftigt koncentrerad till ett fåtal källor och eventtyper. Då finns en risk att en förbättrad benchmark-täckning mest betyder att Upplevio blivit bra på just den snäva referensmängden.

## Ändrat

- Ny `benchmark_sample_quality()` analyserar referensmängden oberoende av Upplevios importerade event.
- Benchmarken grupperas i grova discovery-segment för kvalitetskontroll:
  - Musik
  - Scen & teater
  - Sport
  - Familj
  - Mässa & marknad
  - Mat & dryck
  - Förening & prova på
  - Kultur & museum
- Admin visar hur många av dessa segment som faktiskt finns representerade.
- Segment helt utan referensevent markeras som **Blind fläck**.
- Admin varnar när:
  - referensmängden är liten,
  - en kategori dominerar minst hälften av samplet,
  - en referenskälla dominerar minst 60 procent,
  - viktiga discovery-segment helt saknas.
- Ingen påhittad sammanvägd "benchmark quality score" infördes. En sådan siffra hade skapat falsk precision.

## Viktig avgränsning

Den här releasen lägger inte automatiskt till nya referensevent. Nya benchmarkrader ska fortfarande vara manuellt kontrollerade, daterade och spårbara till verkliga källor. Kvalitetsdiagnostiken visar först *var* referensmängden behöver breddas.

## Produktnytta

Upplevio kan nu skilja två helt olika problem åt:

1. **Upplevio missar event som benchmarken känner till.**
2. **Benchmarken känner själv inte till tillräckligt många typer av event.**

Det minskar risken att teamet optimerar mot en skev testmängd och felaktigt tolkar hög benchmark-täckning som bred lokal eventtäckning.
