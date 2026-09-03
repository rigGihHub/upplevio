# Upplevio v0.10.0 – Pagination & Coverage Diagnostics

Fokus: öka sannolikheten att Upplevio faktiskt hittar fler riktiga event innan nya konsumentfunktioner byggs.

- Ticketmaster hämtas paginerat med säkerhetsgräns och rapporterar om importen är trunkerad.
- Visit Sweden hämtas över flera sidor med tydlig säkerhetsgräns.
- Eventhämtning cachas i 15 minuter i Streamlit för att undvika att varje widget-rerun utlöser en ny serie API-anrop.
- Admin får en ärlig täckningsdiagnos för kommande 30 dagar: antal event, multikällor, saknade koordinater och dublettkandidater.
- Upplevio visar inte en falsk "coverage %" eftersom en oberoende ground-truth-katalog ännu saknas.
