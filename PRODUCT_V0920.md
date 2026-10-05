# Upplevio v0.92.0 – Pålitligare sökfilter

- På söndagar visar ”I helgen” återstående event i den aktuella helgen. Samma datumlogik används för enskilda datum och flerdagarsevent.
- Byte av datumval avslutar tidsbegränsade snabbval som ”Ikväll” och ”Nu & snart”, så att ett dolt filter inte utesluter nästa veckas event.
- ”Rensa snabbval” ligger vid det aktiva snabbvalet. Ändring av budgeten tar bort den inaktuella ”Gratis”-markeringen.
- Budget i kronor jämförs endast med giltiga uttryckliga SEK-priser. Utländska belopp får inte en budgetbonus utan valutakonvertering. Bekräftat gratis fortsätter att matcha och okänt pris räknas aldrig som gratis.
- Upptäcktsvyn och rankingens standarddatum använder Europe/Stockholm även när servern kör UTC.
- Ogiltiga datum kraschar inte listan. Ett ogiltigt eller omvänt slutdatum faller tillbaka till det giltiga startdatumet.
- Appversionen uppdateras även i cache-nyckeln, så att ändringar i importerade moduler används efter uppdatering.

Validering: regressionstester för helgens alla veckodagar, flerdagarsevent, valutor, felaktiga belopp, datum och dygnsskifte. Ett Streamlit AppTest kontrollerar hela flödet ”Ikväll → nästa 7 dagar” och ”Gratis → alla priser” med lokala testevent och isolerade databaser. Ingen ny extern datakälla eller påstådd förbättring av live-datatäckning ingår.
