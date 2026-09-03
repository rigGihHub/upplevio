# Upplevio v0.15.0 — Visit Örebro Discovery Coverage

## Varför denna release
Örebro-benchmarken visade att en stor del av den lokala referensmängden kommer från Visit Örebro. Den publika evenemangskalenderns serverrenderade HTML innehåller inte själva eventposterna, så releasen gissar inte ett dolt API. I stället används två aktuella officiella, redaktionellt underhållna eventlistor som kompletterande discovery-källa.

## Förändringar
- Ny källa: `visitorebro_editorial`.
- Aktuella redaktionella listor för scen/höst och konserter används.
- Parser för `4/9`, `2-5/9`, `1/9-13/9` och `28/9-4/10`.
- Endast datum, titel, plats och uttrycklig gratis-status importeras.
- Saknat pris är fortfarande `unknown`, aldrig gratis.
- Inga artikelbeskrivningar eller bilder kopieras.
- Stabil SHA-1-identitet för importerade poster.
- Överlapp mellan de två redaktionella sidorna dedupliceras inom källan.
- Källan visas separat i source health.

## Datatillit
Poster från redaktionella listor markeras `partial`: Visit Örebro är en officiell destinationskälla, men varje rad har inte korsverifierats mot underliggande arrangör eller biljettkälla i denna adapter. Vanlig multi-source-dedupe kan därefter höja tilliten när samma event finns i exempelvis Conventum/Ticketmaster.

## Avsiktlig begränsning
Den klientrenderade huvudkalendern används inte som automatisk källa förrän dess tekniska gränssnitt/feed har verifierats. Ingen endpoint har antagits eller fabricerats.

## Tester
Nya tester täcker datumformat, månadsskifte, titel/plats, explicit gratis-status, stabila ID:n, att beskrivningar inte kopieras samt intern dedupe mellan redaktionella sidor.
