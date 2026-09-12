
# Upplevio v0.52.0 – Showtimes

## Mål
Göra tidsinformationen mer handlingsbar utan att låtsas veta mer än källorna faktiskt anger.

## Implementerat
- tidsstatus på eventkort när starttid är säker:
  - Börjar snart
  - Ikväll
  - Senare idag
  - Imorgon
  - Startade HH:MM
- Pågår nu visas endast om både start- och sluttid finns och aktuell tid ligger mellan dem
- "Ikväll" i Nightline är nu konservativt:
  - eventet måste vara idag
  - starttid måste vara känd
  - start från 17:00
  - eventet får inte redan ha börjat
- svensk tidszon Europe/Stockholm används explicit
- inga gissade sluttider

## Dataprincip
Saknad sluttid betyder att Upplevio inte kan veta om ett redan startat event fortfarande pågår.
Därför visas "Startade 19:00" i stället för "Pågår nu" när sluttid saknas.
