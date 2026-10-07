# Upplevio v0.93.1 – Färre dubbletter och bredare utbud

Samma evenemang kunde visas flera gånger när källorna skrev titeln olika, utelämnade arena eller lade till en presentatör eller starttid i titeln. Matchningen hanterar nu dessa varianter, bland annat ÖSK/Örebro SK och stand-up/standup. Motstridiga datum, klockslag och specifika arenor blockerar sammanslagning. Snarlika motståndarnamn räcker aldrig för att slå ihop sportmatcher. En mer specifik sportklassificering bevaras vid sammanslagningen.

Återkommande mässor och utställningar med samma titel och arena samlas också på ett kort. Underliggande tillfällen, datum, tider och respektive länkar bevaras i detaljerna. Separata matcher fortsätter att visas var för sig. Gruppering muterar inte importerade event, och samma presentationslogik används i Sparat och nära alternativ.

## Nya aktiva källor

- **Visit Stockholm:** dokumenterat publikt API med paginering och fyra parallella sidförfrågningar efter första sidan. Svenska titlar prioriteras. Faktisk ort, koordinater och uttryckligt schema bevaras; undantagna dagar matchar inte datumfiltret. Alla enskilda starttider bevaras. Priser, biljettlänkar och bildrättigheter antas inte. Eventdata tillskrivs Stockholm Business Region AB med CC BY 4.0 och uppgift om normalisering i detaljerna. Fel på en senare sida behåller framgångsrika sidor och markeras som ofullständig import.
- **ÖSK Bandy:** klubbens offentliga TicketCo-lista med matcher och cuper. Säsongskort filtreras bort. Den synliga svenska starttiden används eftersom JSON-LD:s Z-markering inte stämmer med den lokalt visade tiden. Endast uttryckligt märkta biljettbelopp används.
- **Örebro Badminton:** aktuella officiella matchartiklar med uttrycklig publik inbjudan, Backahallen och publicerade speltider. Artikelns publiceringsdatum används aldrig som matchdatum. Saknat år accepteras bara nära artikelns publiceringsdatum inom samma år; tvetydiga årsskiften hoppas över.

Taxonomin identifierar även badminton, bordtennis, orientering, ridsport, motorsport, kampsport, curling, rugby, gymnastik, triathlon, kajak och skridskor när de uttryckligen anges. Fler kategorier är inte ett påstående om att varje sport nu har liveevent.

## Validering

422 automatiska tester passerar, inklusive regressioner för de observerade dubblettfallen, skilda starttider och motståndare, oförändrade importerade objekt, API-paginering, sidfel, stängda dagar och skillnaden mellan publiceringsdatum och matchdatum. Kontroller mot verkliga källsidor den 7 oktober 2026 gav 14 bandyevenemang, tre badmintonmatcher och 1 717 kommande tillfällen från Visit Stockholm på åtta API-sidor (779 kalenderposter). I Örebros 30-dagarsfönster gav den kontrollerade importen 57 kort efter gruppering. Dessa antal är en ögonblicksbild, inte en garanti för framtida tillgänglighet eller fullständig marknadstäckning.

Källdokumentation: https://api.visitstockholm.com/documentation/
Bandy: https://orebroskbandy.ticketco.events/se/sv
Badminton: https://www.orebrobadminton.com/

## Korrigering vid livekontroll

Livekontrollen fångade ett Streamlit-cachefel när dataklassmodulen laddades om men tidigare importerade källor fortfarande returnerade objekt från den gamla klassen. Båda cachegränserna använder nu vanliga datamappningar och återskapar aktuella event- och källobjekt utanför cachen. Ett regressionstest reproducerar det verkliga pickle-felet via modulomladdning och verifierar återställning med källproveniens. Identiteten för pågående API-datumintervall hålls också stabil när källan flyttar startdatum till nästa dag, så att sparade event behålls.
