
# Upplevio v0.45.0 – Local Source Value Audit

## Mål
Avgöra vilka lokala Örebro-källor som faktiskt förbättrar Upplevio efter dedupe.

## Implementerat
- 30-dagars audit för lokala källor
- representerade event
- unika event
- överlappande event
- unik andel
- antal eventtyper
- eventtyper som endast källans egna event bidrar med i aktuell import
- verifierade bokningsvägar per källa
- bokningstäckning per källa
- adminvy med separat redovisning av varje dimension

## Princip
Ingen artificiell totalscore används. En liten källa kan vara mycket värdefull om den tillför en unik kategori eller lokal long-tail, medan en stor källa kan vara viktig trots hög överlappning eftersom den förbättrar verifiering eller bokningsvägar.

## Nästa beslut
När v0.45 körts på riktig liveimport bör Kulturkvarteret och Wadköping bedömas mot samma dimensioner innan de default-aktiveras.
