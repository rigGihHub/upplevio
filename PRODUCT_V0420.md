# Upplevio v0.42.0 – Tracked Booking Redirect

## Mål
Göra ett verkligt bokningsutklick spårbart utan att försämra användarflödet eller skapa en öppen redirect.

## Implementerat
- signerad redirect-token med HMAC-SHA256
- token innehåller event-id, partner, eventuell kampanj, destination, nonce och utfärdandetid
- bara absoluta HTTPS-destinationer tillåts
- token gäller i 30 minuter
- manipulerad, utgången eller osäker token stoppas
- varje token ger ett deterministiskt `upc_...` click-id
- omladdning av samma redirect ger inte dubbla klick
- redirect behandlas innan källimporter, så bokningsklicket inte behöver vänta på eventhämtning
- automatisk vidarebefordran kompletteras med en manuell "Fortsätt till bokningen"-knapp
- om tracking inte är korrekt konfigurerad används den ursprungliga bokningslänken direkt
- Admin visar om redirectspårningen faktiskt är redo eller ej aktiverad

## Konfiguration
Tracking aktiveras först när båda finns:
- `UPPLEVIO_PUBLIC_URL` – publik HTTPS-adress för appen
- `UPPLEVIO_REDIRECT_SECRET` – minst 32 tecken

## Avgränsning
Detta registrerar bokningsutklick. Bekräftad bokning/provision kräver fortfarande callback eller rapportering från en riktig partner. Inga partneravtal antas finnas.
