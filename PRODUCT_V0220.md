# Upplevio v0.22.0 — Smart zero-result fallback

## Problem
Ett strikt discovery-filter kunde ge 0 träffar och lämna användaren med ett generiskt råd att själv prova andra filter. Det är en dålig kärnupplevelse: Upplevio har redan eventdata och kan därför visa vilka små, tydliga förändringar som faktiskt skulle ge resultat.

## Lösning
v0.22.0 lägger till en konservativ fallback-motor för nollträffar.

När den exakta sökningen ger 0 event kan Upplevio nu prova, i turordning:

- första längre tidsperiod som faktiskt ger träffar
- närmaste större radie som faktiskt ger träffar
- alla priser när användaren satt ett prisfilter
- alla event när `Endast nytt i Upplevio` är aktivt

Sökord och vald eventtyp relaxeras aldrig automatiskt eller i förslagen. De uttrycker stark användarintention och ska inte ignoreras för att fylla skärmen.

Om ingen enskild lättnad ger resultat kan Upplevio som sista steg visa ett tydligt märkt alternativ där både tid och radie breddas. Ingen aktiv widget ändras i bakgrunden.

## UX-princip
Användarens ursprungliga sökning ligger kvar oförändrad. Alternativen visas i en separat sektion `Nära alternativ` med en förklaring av exakt vad som skulle ändras.

Detta undviker den skadliga UX-modellen där en app säger att den visar resultat för exempelvis 25 km men i hemlighet visar event 80 km bort.

## Test
Nya fokuserade tester täcker:

- längre tidsperiod
- minsta fungerande radie
- explicit prisrelaxering
- att okänt pris inte blir gratis
- att sökord och eventtyp aldrig relaxeras
- explicit relaxering av `Endast nytt`
- kombinerad tid/radie endast som sista fallback
