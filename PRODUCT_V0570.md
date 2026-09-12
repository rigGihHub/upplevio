# Upplevio v0.57.0 – Örebro universitet Candidate Source

## Mål
Mäta om Örebro universitets officiella kalendarium tillför publikt relevanta, lokala event som Upplevio annars missar.

## Implementerat
- Örebro universitet tillagd som kandidatkälla, inte som ordinarie discovery-källa.
- Kandidaten hämtar från universitetets kalendarium och publika delkalendrar.
- Parsern kräver explicit `Öppet för alla`.
- Poster som uttryckligen är student-/personal-only avvisas.
- För Örebro-auditen krävs lokal Örebro-signal; Stockholm, Campus Grythyttan och tydligt digitala event avvisas.
- Startdatum och starttid läses endast när de står explicit i kalenderposten.
- Kandidaten går genom samma dedupe- och kandidatbeslutsmotor som Kulturkvarteret och Wadköping.
- Inget universitetsevent läggs i publik discovery i denna release.

## Beslutsprincip
Aktivering sker inte efter en enstaka lyckad hämtning. Kandidatmotorn kräver upprepade snapshots på olika dagar, stabil parser och återkommande unik nytta.

## Begränsning
Parsern är avsiktligt konservativ och kan därför missa publika event som universitetet inte explicit märker `Öppet för alla`. Det är bättre än att läcka interna akademiska aktiviteter in i Upplevios konsumentflöde.
