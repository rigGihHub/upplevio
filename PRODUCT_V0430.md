
# Upplevio v0.43.0 – Booking Funnel Intelligence

## Mål
Mäta vad som faktiskt skapar bokningsintresse utan att blanda ihop visningar, detaljöppningar, bokningsutklick och genomförda köp.

## Implementerat
- funnel: visning → faktisk detaljöppning → bokningsutklick
- visningar dedupliceras per event + filtersignatur + session
- detaljpanelen använder riktig öppna/stäng-interaktion så att "activity_open" betyder ett verkligt användarval
- bokningsutklick från tracked redirect kopplas till partner och click-id
- käll- och eventtypmetadata följer med redirecttoken och lagras med click-id
- historiska bokningsklick kan därför grupperas även om eventet senare försvinner ur aktuell import
- Admin visar funnel totalt samt per källa, eventtyp och bokningspartner
- öppningsgrad och bokningsklick per visning räknas bara när nämnaren finns

## Viktiga avgränsningar
- bokningsklick är inte en genomförd bokning
- konverterad bokning kräver fortfarande partneråterrapportering
- SQLite-data på en Streamlit-deployment är inte en långsiktig analytics-databas och bör senare flyttas till persistent lagring
- funnel-data börjar först byggas när denna release faktiskt används
