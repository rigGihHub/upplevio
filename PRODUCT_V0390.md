
# Upplevio v0.39.0 – Booking Coverage Expansion

## Mål
Utöka säkra direktbokningsvägar och göra bokningstäckning till en mätbar produkt-KPI.

## Implementerat
- City Örebro får detaljside-enrichment för individuella event-URL:er.
- Samma försiktiga CTA-regler som för Conventum används: endast tydliga Boka/Köp biljett/Biljetter-länkar.
- Max 12 detaljsidor per import och parallell hämtning; enrichment får inte fälla grundimporten.
- Ny booking_coverage_report per källa: total, bokningsbara, användbara, svaga, saknade, täckningsgrad och observerade bokningspartner.
- Admin visar bokningstäckning per källa som faktisk KPI inför affiliatearbete.
- Informationslänkar räknas inte som bokningsklick eller bokningstäckning.

## Varför City Örebro nu
Den publika kalendern länkar till individuella eventsidor och flera verifierade detaljsidor har tydliga Köp biljett-vägar. Det ger en säker 1:1-koppling som saknas på breda redaktionella samlingssidor.

## Fortsatt avgränsning
Visit Örebros redaktionella listor enrichas fortfarande inte automatiskt. Vi lägger inte till en källa i bokningsflödet förrän rätt event → rätt detaljsida → rätt bokningslänk kan verifieras.
