# Upplevio v0.20.0 – Local Long-tail & Family Coverage

## Mål
Öka sannolikheten att Upplevio hittar små lokala aktiviteter för barn, unga och familjer som sällan finns i stora biljettkällor.

## Nytt
- Ny officiell kommunal källa: Lov Örebro.
- Import av titel, datumintervall, kort listtext, aktivitetskategorier och uttrycklig gratisstatus.
- Saknat pris förblir okänt.
- Stabil SHA-1-identitet för importerade aktiviteter.
- Säsongstom källa redovisas som säsongstom i stället för fel.
- Pågående flerdagarsevent räknas nu som aktuella även efter startdatumet.
- Datumfiltren Idag, I helgen och kommande perioder arbetar mot hela eventintervallet.

## Viktig begränsning
Lov Örebro är en säsongsbetonad källa och kan legitimt ge noll aktuella poster mellan lovprogram. Platsinformationen i listvyn är inte alltid tillräcklig för exakt avstånd; inga exakta avstånd får fabriceras från ofullständig platsdata.

## Verifiering
- 50/50 automatiserade tester passerar.
- `python -m compileall -q .` passerar.
- Livehämtning i publicerad Streamlit-miljö är inte verifierad.
