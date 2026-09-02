# Upplevio v0.7.0

**Upptäck mer. Upplev mer.**

Upplevio är en gratis-först evenemangsapp för att hitta konserter, mässor, stand-up, samlarkort, retro och andra upplevelser.

## Testa lokalt på Windows
1. Packa upp ZIP-filen.
2. Öppna PowerShell i den uppackade mappen.
3. Kör `python -m venv .venv`.
4. Kör `.\.venv\Scripts\Activate.ps1`.
5. Kör `pip install -r requirements.txt`.
6. Kör `streamlit run app.py`.
7. Webbläsaren öppnar normalt `http://localhost:8501`.

## Viktigt för denna version
- Namnbytt från Evenemangsradar till Upplevio.
- Bevakningsdatabasen är korrigerad och initieras automatiskt.
- Ticketmaster kan kopplas in senare via `TICKETMASTER_API_KEY`.
- Utan API-nyckel går appen fortfarande att testa med tillgängliga källor/demodata.
- Experimentella källor är avstängda som standard.

## Affärsmodell
Upplevio byggs initialt som gratis och annonsfinansierad. Arkitekturen ska senare kunna kompletteras med lågprisabonnemang utan att gratisversionen behöver byggas om från grunden.
