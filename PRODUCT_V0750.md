# v0.75.0 – Parser Fix Impact Audit

- Ny replay-baserad impact audit för v0.74-fixarna.
- Samma eventsida körs genom både pre-v0.74-beteende och aktuell parser.
- Mäter återvunna värden, regressioner och ändrade värden separat.
- Stöd i denna release: `start_time` och `price`, eftersom det var dessa parserregler som ändrades i v0.74.
- Kräver minst tre analyserbara fall och minst två återvunna värden för signalen `Mätbar förbättring i replay`.
- Replay-resultat påstås uttryckligen inte vara verifierad produktionspåverkan innan versionen är deployad och ny import har körts.
- Ingen eventdata eller parserkod ändras av auditen.
