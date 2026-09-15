# Upplevio v0.78.0 – Discovery Layout & Production Collapse

## Problem
Desktopresultaten blev för smala och visuellt hackiga med tre kolumner och separata fullbredds-rader för Detaljer/Spara. Samma teaterproduktion kunde dessutom dominera discovery när den spelades flera datum, eftersom den korrekta eventdata-dedupen kräver samma startdatum.

## Förändring
- Desktopresultat använder två kolumner och bredare innehållsyta.
- Hero, zonrad och filteryta är tätare så användaren når resultaten tidigare.
- Detaljer och Spara ligger i samma kompakta actionrad.
- Generiska rankingorsaker som bara upprepar närhet/tid döljs från kortet; särskiljande orsaker kan fortfarande visas.
- Ny discovery-only `collapse_productions()` håller bara den högst rankade förekomsten av samma scenproduktion i resultatlistan. Övriga spel-datum bevaras på kortet som `+N DATUM`; underliggande eventdata slås inte ihop.
- Produktioner måste vara scen/show/teater-liknande, ha mycket lik titel och icke-motsägande stad/venue för att kollapsas. Sportevent kollapsas inte över datum.

## Viktig avgränsning
Detta ersätter inte eventdata-dedupen. Separata matcher, konserter med olika titlar och samma produktion i motsägande stad/venue ska fortsatt behandlas separat.
