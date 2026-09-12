# Upplevio v0.28.0 — Coverage Gap Intelligence

## Varför

Benchmarken kunde tidigare visa hur stor del av den manuellt kontrollerade referensmängden som Upplevio hittade och vilka enskilda event som missades. Det var användbart för QA, men svagt som prioriteringsstöd: den sa inte tydligt vilka typer av event, platser eller referenskällor som stod för luckorna.

## Ändrat

- Benchmarkrapporten räknar nu täckning per kategori.
- Benchmarkrapporten räknar nu täckning per venue/plats.
- Missade kategorier sorteras efter antal missade referensevent.
- Missade venues sorteras efter antal missade referensevent.
- Referenskällor med luckor sorteras efter antal missade referensevent.
- Admin visar en ny sektion "Var finns luckorna?" med kategori- och källgap.
- Venue-gap ligger i en separat expander för att hålla Admin-vyn kompakt.
- Tabellen med missade benchmark-event visar nu även kategori.

## Produktprincip

Luckdiagnostiken är ett beslutsunderlag för nästa källspår, inte ett påstående om hela Örebros eventmarknad. Benchmarken är fortfarande en liten, manuellt kuraterad sample och får inte användas som generell marknadstäckningsstatistik.

## Varför detta är bättre än att bara lägga till fler källor

Det gör att Upplevio först kan se vilken typ av lucka som faktiskt finns och därefter avgöra om nästa källintegration är motiverad. En källa som inte fyller en observerad lucka ska inte prioriteras bara för att den råkar vara enkel att integrera.
