# Upplevio v0.14.0 — Local Official Source Pilot

## Mål
Öka verklig lokal datatäckning där v0.13.0-benchmarken visar en konkret lucka, utan att lägga till nya konsumentfunktioner.

## Ändringar
- Conventums officiella arrangemangskalender är en lokal pilotkälla för Örebro.
- Importen är konservativ: endast poster med eventlänk, titel och tolkbart datum accepteras.
- Källa och kvalitet markeras tydligt; detaljsidan betraktas inte som korsverifierad bara för att kalenderposten hittats.
- Fel i Conventum-källan får inte stoppa Ticketmaster/Visit Sweden eller resten av appen.
- Benchmarkvyn bryter nu ned träffar och missar per referenskälla.
- Officiella HTML-källors event-ID har ändrats från instabil Python `hash()` till stabil SHA-1-identitet.

## Varför Conventum först?
v0.13.0:s oberoende Örebro-benchmark innehåller många event från Conventums officiella kalender. Det är därför en mer direkt täckningsåtgärd än att bygga fler filter, rekommendationsfunktioner eller generella datakällor.

## Begränsningar
- Livehämtning från Conventum kan inte verifieras i den lokala testmiljön eftersom den saknar internet/DNS.
- Kalenderns publika innehåll och aktuella septemberposter har verifierats via webbsökning 2026-09-03, men parsern är testad mot representativ HTML-fixture, inte ett sparat live-HTML-svar.
- Juridisk återanvändningsbedömning av full eventdata/bilder är inte genomförd. Importen använder därför endast textmetadata/länkar och inga externa bilder från Conventum.
