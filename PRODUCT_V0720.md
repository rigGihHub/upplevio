# Upplevio v0.72.0 — Evidence Batch Audit

- Batchgranskar upp till nio konkreta gap-fall för samma källa och detaljfält.
- Rena enkällsevent ligger först för starkare parserproveniens.
- Klassar återkommande parserkandidat först när minst tre sidor är analyserbara och minst tre parserkandidater utgör minst 60 procent.
- Hämtningsfel exkluderas från kandidatandelen och redovisas separat.
- Read-only: inga event eller parsers ändras automatiskt.
- Kör små batcher parallellt (max fyra workers i UI) för rimlig adminlatens.
