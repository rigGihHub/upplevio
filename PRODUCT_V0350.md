# Upplevio v0.35.0 – Result Trust & Noise Suppression

## Syfte
Skilj legitim long-tail med tunn metadata från tydligt parser-/navigationsbrus.

## Förändringar
- Ny `result_trust.py` med konservativ brusklassificering.
- Endast högkonfidens-brus döljs automatiskt från discovery:
  - navigations-/knapptext som `Läs mer`, `Köp biljett`, `Boka nu`
  - titlar som bara är datum eller tid
  - URL-liknande titlar
- Tunn metadata, saknad starttid och generiska men möjliga eventtitlar döljs inte.
- Osäkra signaler får status `review` och visas endast i Admin.
- Admin visar antal dolda brusposter, granskningsposter och källa för problemen.
- Källors råtitlar kan ge review-signal vid tydlig sammanslagningsavvikelse, men aldrig automatisk suppression.

## Produktprincip
Noise suppression ska skydda användaren från parserartefakter utan att gynna stora välstrukturerade biljettkällor framför små lokala arrangörer.
