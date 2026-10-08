# Upplevio v0.94.1 – Rättad rendering av evenemangsdetaljer

Detaljrutan renderas direkt som HTML. Tidigare kunde tomma rader för saknad insläppstid eller åldersgräns göra att Markdown visade källinformation och fler datum som rå HTML i ett kodblock. Även beskrivningar med tomma rader och indrag visas nu som text i rutan. Publicerat innehåll HTML-escapas fortsatt.

Två Streamlit AppTest-fall öppnar ett återkommande teaterarrangemang och kontrollerar källinformation, alternativa datum och länkar, både med och utan valfria uppgifter. De verifierar också att beskrivningens specialtecken visas som text. Sporturvalet med endast lagsporter från v0.94.0 behålls.
