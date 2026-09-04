# Upplevio v0.19.0 – Local Sports Coverage

## Mål
Öka faktisk lokal eventtäckning i Örebro genom officiella sportkällor, utan att lägga till breda eller osäkra scrapers.

## Nytt
- ÖSK Fotboll officiella herr- och damscheman som lokal discovery-källa.
- Endast hemmamatcher i Behrn Arena importeras; bortamatcher filtreras bort.
- Örebro Hockey officiellt publicerade spelschema som pilotkälla.
- Endast hemmamatcher i Behrn Arena importeras.
- Stabil SHA-1-identitet för sportevent.
- Sportevent får kategori/tags Sport, Fotboll/Hockey och lag/serie där källan stödjer det.
- Saknat biljettpris förblir `unknown` och får aldrig tolkas som gratis.
- Sporttaxonomin känner nu igen bland annat fotboll, hockey, SHL, Superettan och Elitettan.

## Produktbeslut
Sport prioriterades eftersom officiella lokala spelscheman innehåller publika event som generella biljett- och destinationskällor inte kan förväntas täcka fullständigt. Det stärker kärnuppgiften "vad händer i närheten?" mer än ytterligare personaliseringsfunktioner.

## Begränsningar
- ÖSK-parsern är testad mot representativ HTML och baserad på den officiella sidans nuvarande struktur, men livehämtning är inte verifierad från Streamlit-miljön.
- Örebro Hockey är uttryckligen pilot. Nuvarande implementation använder ett officiellt publicerat spelschema; en dokumenterad maskinläsbar kalender/feed bör föredras om en sådan verifieras senare.
- Ingen biljettprisuppskattning görs.
- Ingen ungdoms-/breddidrott importeras i denna release.

## Verifiering
- 46/46 automatiserade tester passerar.
- `python -m compileall -q .` passerar.
- Ingen live browser/API-verifiering har gjorts i appmiljön.
