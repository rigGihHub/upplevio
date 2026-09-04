# Upplevio v0.21.0 – Source Health Guardrails

## Syfte
Upptäcka tysta fel i eventdata innan de blir ett osynligt produktproblem. Upplevio ska inte se frisk ut när en viktig källa slutat leverera eller när en parser tappat centrala fält.

## Förändringar
- Ny `source_health.py` med konservativ diagnostik av aktuell import.
- Skiljer på `Fel`, `Kontrollera`, `Delvis`, `Pilot`, `Säsongstom`, `Ej konfigurerad` och `OK`.
- 0 importerade event från en normalt aktiv källa flaggas för kontroll.
- Säsongskällan Lov Örebro får vara tom utan falskt alarm.
- Hög andel saknade länkar/orter eller saknade startdatum kan indikera parserregression.
- Admin visar sammanfattning och diagnos per källa.
- Vanliga användare får endast en lågmäld varning när dataläget faktiskt är degraderat.
- Rå exceptiontext visas inte längre i källstatus. Detta minskar risken att URL:er, query-parametrar eller API-hemligheter råkar exponeras.

## Medveten avgränsning
v0.21.0 analyserar den aktuella importen. Den påstår inte att volymförändringar över tid är fel. Historisk baseline, t.ex. ”Conventum brukar ge 18–25 event men ger nu 3”, kräver schemalagda bakgrundsimporter och persistent körhistorik och byggs inte halvvägs i Streamlit-reruns.
