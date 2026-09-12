# Upplevio v0.71.0 — Parser Fix Evidence

## Syfte
Göra Gap → fix-workflowet diagnostiskt: skilj parsermiss från verklig källdatalucka innan ny parserkod skrivs.

## Nytt
- Ny `parser_fix_evidence.py` för evidensbaserad, read-only granskning av en vald eventsida.
- Admin kan välja ett konkret gap-fall och aktivt klicka **Granska sidan efter evidens**.
- Resultat klassas transparent som bland annat `Parserkandidat`, `Källan verkar sakna uppgiften`, `Källan saknar exakt värde`, `Manuell granskning` eller `Kunde inte granska`.
- Exakta tider, uttryckligt märkta priser, åldersgränser, dörrtider och venue-evidens återanvänder Upplevios konservativa extraktionsregler.
- Durationstext som `ca 60 minuter` blir aldrig en exakt sluttid.
- Evidensvyn ändrar aldrig Event, enrichment eller parser automatiskt.
- Publik HTTP/HTTPS-validering skyddar diagnostikhämtningen från lokala/privata adresser.
- Bokningslänkar lämnas till befintlig separat booking-safety-logik.

`APP_VERSION = "0.71.0"`
