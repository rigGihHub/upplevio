
# Upplevio v0.55.0 – Go Now

## Mål
Göra det lätt att hitta event som ligger tillräckligt nära i både tid och geografi för att vara värda att kontrollera direkt.

## Implementerat
- nytt Nightline-val: Go Now
- kräver känd starttid och beräkningsbart avstånd från vald stad
- använder en konservativ planeringsmarginal, inte faktisk restid:
  - upp till 10 km: minst 45 minuter till start
  - upp till 25 km: minst 75 minuter till start
  - upp till 50 km: minst 120 minuter till start
- maximalt 240 minuter till start
- upp till tre högst rankade kandidater visas först
- samma organiska discovery-ranking används; ingen separat Go Now-score
- snabbfakta visar tid till start, avstånd, planeringsnotis, pris och om bokningslänk finns
- tracking-surface: `go_now`

## Viktigt
Go Now betyder inte "du hinner". Appen känner inte trafik, färdsätt, parkering eller användarens exakta position. UI:t säger därför uttryckligen att faktisk restid måste kontrolleras.
