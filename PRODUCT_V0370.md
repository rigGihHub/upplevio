
# Upplevio v0.37.0 – Booking Intent & CTA Quality

## Mål
Göra Hitta → Inspireras → Boka trovärdigt innan affiliateintäkter aktiveras.

## Implementerat
- konservativ klassning av boknings-, biljett-, tid- och informationslänkar
- Boka visas för explicit booking_url
- Köp biljett visas när biljettvägen är tydlig
- Se tider används för schema-/kalendervägar
- Läs mer används när vi bara kan styrka information, inte bokning
- generella startsidor flaggas som svaga CTA-vägar
- bokningsutklick räknas endast för CTA som faktiskt klassas som bokning/biljett
- Admin visar bokningsbara, användbara, svaga och saknade externa vägar
- organisk ranking är fortsatt helt separerad

## Varför
Aktuella lokala källor visar både riktiga "Köp biljetter"-flöden och redaktionella sidor som länkar vidare.
Upplevio får inte kalla varje extern länk "Boka"; det skulle både försämra UX och förstöra framtida funnel-data.

## Avgränsning
URL-heuristik är en säker grund, inte slutmålet. Nästa nivå är källspecifika parsers som kan fånga
den faktiska biljett-/bokningslänken från respektive eventdetaljsida.
