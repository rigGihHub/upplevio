# Upplevio v0.60.0 – Community & Association Frontier

## Produktmål
Bredda Upplevios long-tail discovery mot lokala community- och föreningsarrangemang utan att sänka datakvaliteten eller fylla flödet med återkommande intern verksamhet.

## Källgranskning
- Örebro bibliotek är relevant, men den publika evenemangssidan laddar event via JavaScript och ger i nuläget för svagt/stabilt råunderlag för en konservativ server-side parser. Källan aktiveras därför inte ens som kandidat i denna release.
- Svenska kyrkan i Örebro har en aktuell officiell kalender med bland annat konserter, föreläsningar, samtal, visningar och vernissager, men också mycket gudstjänst-, bön- och gruppinnehåll.

## Ändringar
- Ny candidate-only källa: Svenska kyrkan i Örebro.
- Dedikerad strikt parser för publikt discovery-värde.
- Kräver explicit datum och stark kultur/community-signal.
- Accepterar bland annat konsert, föreläsning, författaraktivitet, vernissage, visning/guidning, samtal/föredrag, marknad, festival, utställning och retreat.
- Filtrerar uttryckligen bort gudstjänst, högmässa, vanlig mässa, morgonbön, bönegrupp, bibelstudium, körövning/repetition, medlemsmöte och tydligt slutna aktiviteter.
- Numeriska datum som 9/9 stöds konservativt för denna källa.
- Starttid används bara när explicit klockslag hittas.
- Gratisstatus sätts bara vid uttrycklig text som Gratis, Ingen kostnad eller Fri entré.
- Candidate Value Audit/Candidate Decision Engine används oförändrat: källan påverkar inte publik discovery innan flera riktiga snapshots visar återkommande unik nytta.

## Kritisk produktprincip
Religiös eller organisatorisk tillhörighet är inte ett discovery-kriterium. Källan används enbart som officiell arrangörskälla för publika aktiviteter som kan vara relevanta även för en bred allmänhet. Vanlig löpande församlingsverksamhet ska inte fylla Upplevio.

## Nästa logiska steg
Outdoor & Nature Frontier. Prioritera officiella lokala källor som Naturens hus/Oset-Rynningeviken/Karlslund och bygg kandidatimport endast där datum, plats och publik relevans kan verifieras utan gissningar.
