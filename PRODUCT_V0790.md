# Upplevio v0.79.0 — Card Hierarchy & Runtime Guardrails

## Mål
Färdigställa strukturpasset från v0.78 så discovery blir lugnare, jämnare och robust på desktop.

## Förändringar
- Fixar ett runtimefel i v0.78 där två skapade kolumner fortfarande indexerades med modulo 3.
- Huvudresultat och Sparat använder nu faktisk kolumnlängd vid rendering.
- Korttitlar begränsas till två rader för jämnare rytm mellan kort.
- Upprepade scenproduktioner visar en kompakt `+N DATUM`-badge.
- Detaljer är fortsatt huvudaction medan Spara reduceras till en kompakt hjärtknapp med tooltip.
- Desktopytan breddas till 1520 px.
- Festivalzonerna behålls som visuell identitet men deras förklarande brödtext döljs i översiktsläget.
- Käll- och trustinformation finns kvar längst ned på kortet; discovery-rankingens generiska förklaringar fortsätter vara nedtonade.

## Avgränsning
Denna release förändrar inte underliggande eventdedupe, rankingmodell eller källimport. Cross-date-kollapsen från v0.78 är fortfarande en presentationsregel för återkommande scenproduktioner.
