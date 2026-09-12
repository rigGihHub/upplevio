# Upplevio v0.70.0 — Gap-to-Fix Workflow

## Varför
v0.69 kunde rangordna nästa detaljlucka, men utvecklaren behövde fortfarande själv leta fram vilka konkreta event och sidor som låg bakom signalen. v0.70 gör prioriteringen operativ utan att automatisera bort proveniensbedömningen.

## Nytt
- Ny `detail_gap_workflow.py` som översätter källa + fält till konkreta eventfall i aktuell 30-dagarsimport.
- Enkällsevent visas först eftersom parseransvaret där är renast.
- Fler-källevent använder i första hand den valda källans egen `SourceRecord.source_url`, inte blint eventets globala `official_url`.
- Admin får väljare för de högst prioriterade luckorna och en granskningslista med datum, event, plats, URL-underlag och källor.
- Workflow-sammanfattning visar antal fall, rena enkällsfall och URL-täckning.
- Inga nya HTTP-anrop görs av workflowet; det diagnostiserar redan importerad data.
- Ingen dold totalscore införs.

## Trust-regler
- Ett fler-källeevent påstås inte vara ett rent parserfel hos vald källa.
- URL-proveniens visas explicit.
- Demo-event och event utanför auditens horisont ignoreras.
- Saknat fält definieras med samma semantik som detaljauditen.

## Version
`APP_VERSION = "0.70.0"`
