
# Upplevio v0.41.0 – Conversion Attribution Foundation

## Mål
Förbereda verklig attribution från bokningsutklick till senare partnerkonvertering.

## Implementerat
- unikt `upc_...` click-id per bokningsutklick
- klicket kan kopplas till event, bokningspartner och sponsringskampanj
- separat lagring för outbound clicks och partnerkonverteringar
- konverteringsstatus: pending / confirmed / rejected / refunded
- ordervärde och provisionsvärde kan lagras separat
- okända click-id avvisas
- partner_conversion_id gör callbacks idempotenta
- Admin visar spårade klick, rapporterade konverteringar och bekräftade bokningar
- rapportering per partner finns för framtida partnerdashboard

## Viktig avgränsning
Det finns ännu ingen aktiv redirect-endpoint eller webhook från en riktig bokningspartner.
Modellen är därför teknisk grund, inte ett påstående om fungerande end-to-end affiliateattribution i liveappen.
