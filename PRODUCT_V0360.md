
# Upplevio v0.36.0 – Booking & Revenue Foundation

## Mål
Förbered framtida intäkter utan att göra nuvarande discovery reklamigare.

Prioritering:
1. bokning / affiliate
2. relevanta sponsrade upplevelser
3. diskreta programmatiska annonser

## Implementerat
- kommersiella metadatafält på Event med bakåtkompatibla defaults
- separat sponsor-policy som endast får välja bland redan organiskt relevanta kandidater
- kampanjdatum, geo, målgrupp, prioritet, kampanj-ID och företag
- booking_url, booking_partner, affiliate_program och affiliate_ref
- mättaxonomi för impression, aktivitetsbesök, CTA, bokningsutklick, sponsor och annons
- lokal SQLite-baserad eventlogg som teknisk MVP-grund
- företagsmetrics för impressions, aktivitetsbesök, bokningsklick och CTR
- inaktiverat annonsinventarium för native/display
- boknings-CTA i eventdetaljer när boknings-/biljettlänk finns
- organisk ranking använder inga sponsor-/annonsfält
- lokalt tips är en redaktionell signal och påverkar inte rankingen

## Viktiga avgränsningar
- inga annonser är aktiverade
- inga sponsrade placeringar injiceras ännu i discovery
- ingen demo-statistik visas
- genomförd bokning kan inte mätas förrän partner kan återrapportera konvertering
- företagsvyn är datamodell/administrativ beredskap, inte publik self-service eller auth
