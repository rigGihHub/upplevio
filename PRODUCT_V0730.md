# v0.73.0 – Parser Fix Recommendation

Batch-evidens kan nu översättas till ett konkret, granskningsbart parserförslag när evidensen verkligen är återkommande.

- pekar ut exakt modul och funktion som bör granskas
- sammanfattar hur många analyserbara sidor som stödjer fixen
- visar upp till tre konkreta evidensexempel
- kräver positiva och negativa regressionstester
- rekommenderar aldrig en fix vid blandad/för liten evidens
- ändrar aldrig parserkod eller eventdata automatiskt

Rekommendationerna är deterministiska mallar per detaljfält. De skapar ingen generell AI-gissning om kodändringar.
