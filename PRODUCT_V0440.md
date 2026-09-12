
# Upplevio v0.44.0 – Örebro Source Expansion

## Mål
Öka faktisk lokal datatäckning med starka officiella förstahandskällor.

## Integrerat
- Örebro Konserthus, default enabled
- Örebro Teater, default enabled
- båda körs som separata source tasks med befintlig failure isolation
- Örebro Konserthus läser individuella officiella eventsidor
- explicit datum, tid och pris tas med; saknat pris förblir okänt
- gratis markeras bara vid explicit fri entré/gratis/kostnadsfri biljett
- Örebro Teater läser officiellt kalendarium och bevarar separata föreställningsdatum
- befintlig dedupe får hantera överlapp mot Visit Örebro, City Örebro och biljettkällor
- Konserthus-events går genom befintlig säkra booking enrichment

## Kandidater som inte slogs på ännu
- Kulturkvarteret
- Wadköping

De är fortsatt intressanta, men läggs inte till samtidigt. Först bör v0.44 mäta unik eventnytta och överlapp för de två nya förstahandskällorna. Det minskar risken att vi ökar parserbrus och dubletter snabbare än verklig täckning.
