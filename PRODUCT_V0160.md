# Upplevio v0.16.0 – Multi-source merge & source trust

## Mål
Samma verkliga event från flera källor ska visas som ett event med bevarad proveniens och begriplig verifieringsnivå, utan aggressiva felmerge.

## Ändringar
- Konservativ dedupe med hård spärr vid motstridig stad eller datum.
- Exakt source/external-id betraktas som samma källpost.
- Source records dedupliceras men bevaras vid merge.
- Fält fylls från kompletterande källor och högre källförtroende får företräde vid vissa textfält.
- Prisinformation saknas = aldrig gratis. Explicit priskonflikt flaggas.
- Verifieringsmodell: `Källverifierad`, `Bekräftat från N källor`, `Behöver verifieras`.
- Legacy-värdet `verified` normaliseras bort i dedupe-flödet.
- Eventkort visar verifieringsstatus i stället för en teknisk källräknare.

## Medveten begränsning
Dedupe är fortfarande O(n²) och lämnas så för nuvarande MVP-volymer. Ingen ML/fuzzy entity resolution införs innan data visar att det behövs.
