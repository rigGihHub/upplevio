# Upplevio v0.11.0 – Core discovery simplification

Målet i v0.11.0 är att göra Upplevio till en konsumentprodukt i stället för ett tekniskt eventverktyg.

## Ändrat
- Huvudflödet är nu: Var? → När? → Hur långt? → Budget?
- Tekniska datakällor har flyttats bort från huvudflödet.
- Radar/Upptäck/Listvy/Bevakningar har inte längre egna huvudflikar.
- Startsidan visar inte längre dashboard-mätetal eller sju tomma dagkort.
- Pris är förstaklassdata i Event-modellen.
- Ticketmaster `priceRanges` normaliseras till min/max/currency/status.
- Okänt pris behandlas aldrig som gratis eller som "under budget".
- Extern text HTML-escapas innan den renderas i egna HTML-kort.
- Konsumentnavigeringen är reducerad till Vad händer?, Sparat och Admin.

## Medvetna begränsningar
- Visit Sweden-pris parsas ännu inte innan deras verkliga linked-data-format verifierats.
- Pris saknas därför på många event och visas uttryckligen som "Pris saknas".
- Bevakningsdata finns kvar i databasen men är borttagen från huvudflödet tills den faktiskt matchar och levererar träffar.
- Admin finns kvar som flik under MVP-fasen; i en publik produkt bör den senare rollskyddas.
