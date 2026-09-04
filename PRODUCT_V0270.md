# Upplevio v0.27.0 — Source Latency & Failure Isolation

## Varför

Källimporterna kördes tidigare sekventiellt. En långsam källa kunde därför lägga sin väntetid ovanpå alla andra källors väntetid innan användaren fick resultat.

## Ändrat

- Oberoende källor startas nu parallellt via en liten `ThreadPoolExecutor`-gräns.
- Ett fel i en källa isoleras till den källans health-rad; lyckade källors event behålls.
- Källordningen i diagnostiken är deterministisk även om hämtningarna blir klara i annan ordning.
- Inga automatiska retries har lagts till. Det undviker att en trasig upstream belastas mer och gör väntan längre.
- Befintliga HTTP-timeouts i respektive adapter behålls. Ingen påhittad millisekundsvinst påstås.
- Streamlits 15-minuters cache behålls. Persistent stale-while-revalidate införs inte ännu, eftersom det kräver en tydlig persistent snapshot-/refreshmodell och bör inte byggas halvt.

## Viktig avgränsning

Detta gör inte externa källor snabbare. Det tar bort den onödiga sekventiella väntan mellan oberoende källor och gör fel mer isolerade.

Liveprestanda och faktisk nätverkslatens är inte verifierade förrän releasen deployats.
