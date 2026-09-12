# Upplevio v0.68.0 – Detail Coverage & Trust Audit

## Varför
v0.65–0.67 gav eventmodellen verifierad sluttid, dörr-/insläppstid, åldersgräns, bättre venue och försiktig prisextraktion. Nästa steg är att mäta hur mycket av den praktiska detaljdatan som faktiskt finns i aktuell import – per representerad källa – innan mer parserarbete prioriteras.

## Nytt
- Ny `detail_coverage.py` med 30-dagars audit av färdiga deduplicerade event.
- Mäter separat: starttid, sluttid, komplett tidsintervall, plats, preciserad plats, känd prisstatus, åldersgräns, dörrtid och bokningslänk.
- Visar antal enkällsevent som renare attribueringssignal.
- Transparenta kvalitetsflaggor, exempelvis `Sluttid saknas ofta`, `Plats behöver förbättras`, `Pris saknas ofta`, `Stark praktisk data` och `För lite data`.
- Ingen syntetisk totalscore.
- Admin får ny sektion **Detaljtäckning & trust · 30 dagar** med fyra toppmått och tabell per källa.

## Trust-princip
Efter dedupe kan ett event representeras av flera källor och detaljfältets exakta proveniens är då inte alltid känd. Auditen beskriver därför kvaliteten på färdiga event som källan representerar, inte att just den källan säkert levererade varje fält. Enkällsevent visas separat för att göra den begränsningen tydlig.

## Produktprincip
- Okänt pris räknas aldrig som gratis.
- Generiska platser som `Örebro` eller `Conventum` räknas inte som preciserad venue.
- Ingen ny publik UI-komplexitet; detta är ett admin-/prioriteringsverktyg.
- Auditen är en snapshot av aktuell import, inte ett påstående om marknadstäckning.
