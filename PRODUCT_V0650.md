# Upplevio v0.65.0 – Showtime End Time Foundation

- Event-modellen har nu ett riktigt frivilligt `end_time`.
- Sluttid fylls bara när källan uttryckligen anger den. Ingen varaktighet gissas.
- `Pågår nu` får därmed ett riktigt datakontrakt genom modellen i stället för ett dynamiskt attribut.
- Visit Sweden kan bevara klockslag i ISO `startDate`/`endDate` när de finns.
- Karlslund och Makeriet kan bevara explicita tidsintervall, inklusive `11–16` och `20:00–23:00`.
- Eventkort kan visa `start–slut` när båda tiderna är kända.
- Dedupe bevarar verifierad sluttid från en kompletterande källa.
- Saknad sluttid förblir saknad; Upplevio hävdar då inte att ett redan startat event fortfarande pågår.
