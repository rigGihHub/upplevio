# Upplevio v0.25.0 – Top-result Ranking Quality

## Mål
Göra topp 5–10 mer användbara när många event matchar, utan att bygga en ogenomskinlig rekommendationsmodell eller låta variation slå explicit relevans.

## Förändring
Basrankingen är fortsatt samma förklarbara modell: sökfråga, avstånd, tid, pris, intressen och en liten källtillits-tiebreak. Efter basrankingen görs en försiktig presentation-reranking endast bland nästan likvärdiga kandidater.

Små diversitetspåföljder kan ges när flera av de senaste toppresultaten har samma eventtyp, samma venue eller samma datum. Kandidater utanför ett smalt score-band kan inte hoppa förbi ett klart bättre event. Diversifieringen ändrar inte eventets score eller dess förklaringar.

## Varför
En strikt poängsortering kan ge fem snarlika konserter från samma venue överst trots att ett nästan lika relevant sport-, familje- eller teaterevent finns direkt efter. Det kan få Upplevio att kännas smalare än datan faktiskt är. Samtidigt vore aggressiv diversifiering farlig eftersom den kan dölja det användaren uttryckligen sökt efter.

## Guardrails
- Endast topp 10 diversifieras.
- Endast kandidater inom 8 poäng från bästa kvarvarande kandidat får konkurrera om nästa plats.
- Explicit relevans och stora skillnader i närhet/tid skyddas.
- Ingen slumpmässighet.
- Ingen ny användarprofil eller ML-modell.

## Verifiering
- 73/73 tester passerar.
- compileall passerar.
- ZIP-integritet kontrolleras vid paketering.
- Live Streamlit/mobile/API är inte verifierat förrän releasen deployats.
