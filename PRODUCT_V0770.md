# Upplevio v0.77.0 — Discovery Data Quality Gate

## Mål
Skydda huvuddiscovery från event med trasig central dataintegritet utan att missgynna legitima long-tail-event som bara saknar sekundär metadata.

## Förändringar
- Ny `discovery_data_quality.py` med konservativ kvalitetsgrind.
- Organisk ranking får ett score-tak för event där titel/startdatum är ogiltigt, slutdatum motsäger startdatum eller både venue och ort saknas.
- Event tas inte bort av kvalitetsgrinden; de kan fortfarande hittas och visas.
- Saknad starttid, sluttid, pris, åldersgräns, dörrtid och bokningslänk ger inget rankingstraff.
- Prisstatus som motsäger prisfält flaggas för admin-granskning men påverkar inte ranking.
- Admin visar hur många event som passerar, får begränsad ranking eller behöver konsistensgranskning.

## Produktprincip
Kvalitetsgrinden ska stoppa trasig kärndata från att dominera topplistan, inte göra strukturerad metadata till ett krav för att små arrangörer ska få synas.
