# Upplevio v0.24.0 — First 10 Seconds

## Mål
Korta tiden från öppnad app till en begriplig, relevant resultatlista utan att ta bort kontroll eller lägga till ny produktkomplexitet.

## Förändringar
- Hero ändrad från generiska “Vad händer?” till kärnlöftet “Hitta det du inte vill missa.”
- Tydlig instruktion i hero: börja med plats och tid; övriga val är valfria.
- De fyra kärnvalen ligger i två lugna rader: Var → När → Hur långt → Budget.
- Standardläge ändrat till Örebro · Nästa 7 dagar · 50 km · Alla priser.
- Tidigare standard 30 dagar/100 km gav bredare men mindre omedelbart relevanta resultat.
- Intressen flyttade från ett eget expandersteg till “Fler val”.
- Sök, eventtyp, endast nytt och intressen samlas nu på ett ställe för avancerad fördjupning.
- Resultatsammanfattning visar aktiv discovery-kontext, exempelvis “Örebro · Nästa 7 dagar · inom 50 km”.
- Ingen automatisk platsåtkomst, konto- eller onboardingfunktion har lagts till; första flödet hålls snabbt och transparent.

## Produktprincip
Första 10 sekunderna ska kräva så få beslut som möjligt. Standardläget ska vara användbart direkt, men användaren ska tydligt se och kunna ändra varje kärnval.

## Verifiering
- 69/69 pytest-tester passerar.
- `python -m compileall -q .` passerar.
- Live Streamlit/mobilbrowser är inte verifierad förrän releasen pushas/deployas.
