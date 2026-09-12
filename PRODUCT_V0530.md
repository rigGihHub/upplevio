
# Upplevio v0.53.0 – Tonight Mode

## Mål
Göra frågan "Vad kan jag göra ikväll?" till ett mycket snabbt mobilbeslut.

## Implementerat
När Nightline-valet Ikväll är aktivt:
- de tre högst rankade kvällseventen visas först
- samma befintliga discovery-ranking används; ingen separat Tonight-score skapas
- varje toppval får:
  - beslutslabel
  - känd starttid
  - avstånd från vald stad om tillgängligt
  - prisstatus/pris
- övriga kvällsevent visas under "Fler ikväll"
- toppval registreras med surface `tonight` i befintlig engagement/funnel-logik
- favoriter och detaljer fungerar även i Tonight Mode

## Princip
Tonight Mode förändrar presentationen, inte den organiska rankingen.
Det gör upplevelsen snabbare utan att skapa en andra källa till "vad som är bäst".
