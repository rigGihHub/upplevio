
# Upplevio v0.51.0 – Nightline Navigation

## Mål
Göra discovery snabbare med festivalguide-liknande snabbval utan ny komplex filtreringsmotor.

## Snabbval
- Ikväll
- I helgen
- Gratis
- Nära vald stad
- Hidden Gems
- För familjen

## Beteende
- Ikväll använder "Idag" eftersom många källor saknar säker sluttid
- I helgen återanvänder befintligt datumfilter
- Gratis återanvänder befintligt prisfilter
- Nära vald stad sätter 25 km runt vald/default stad
- Hidden Gems använder befintlig festivalzon/lokal discovery-signal
- För familjen använder Family Zone
- snabbval kan rensas explicit

## Viktigt
Ingen GPS används och appen påstår därför inte att den känner användarens exakta position.
Ranking, datakällor, dedupe och bokningslogik är oförändrade.
