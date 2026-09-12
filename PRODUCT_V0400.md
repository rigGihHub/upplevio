
# Upplevio v0.40.0 – Booking Partner Attribution

## Mål
Göra bokningsutklick kommersiellt mätbara utan att blanda ihop bokningsplattform med affiliateavtal.

## Implementerat
- normaliserat partnerregister för Ticketmaster, Tickster, Eventim, Nortic och Billetto
- subdomäner matchas mot rätt partner
- okända domäner klassas som direkt/annan bokningsdestination, inte som påhittad partner
- booking_partner_key, booking_partner_domain och affiliate_status på Event
- affiliate_status är separat från partneridentitet och börjar som `unassessed`
- enrichment skriver normaliserad partnerattribution
- deduplicerade event attribueras centralt före UI/rapportering
- Admin visar bokningspartner, volym, typ och affiliate-status
- booking coverage använder normaliserade partnernamn

## Viktig princip
Att Upplevio kan identifiera Tickster/Eventim/Ticketmaster betyder inte att ett affiliateavtal finns.
Ingen partner markeras affiliate-aktiverad utan faktisk verifiering eller avtal.
