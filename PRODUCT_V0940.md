# Upplevio v0.94.0 – Endast lagsporter i sportutbudet

Badmintonkällan hämtas inte längre och är markerad som avstängd i källregistret. Sportposter från andra källor måste också kunna identifieras som lagsport för att visas. Tennis, padel, golf, badminton, löpning och andra individuella sporter och sportaktiviteter filtreras bort.

Urvalet använder publicerad titel, kategori, taggar och beskrivning. Exempel på kvarvarande sporter är fotboll, ishockey, bandy, basket, handboll, volleyboll, innebandy, amerikansk fotboll, rugby och curling. Identifierade lagtävlingar i Counter-Strike, League of Legends och Dota 2 kan också visas. En generell sportmarkering eller ordet lagmatch räcker inte för att fastställa sportgren. Kalenderposter utan tillräcklig information om sportgren döljs.

Policyn tillämpas på den gemensamma listan för Upptäck, Sparat, snabbval och nära alternativ, efter att källornas dubbletter har slagits ihop. Kultur, konserter och övriga evenemang behålls. Tekniska käll- och datakvalitetsvyer kan fortfarande innehålla råa sportposter för diagnostik. Inga sparade poster raderas ur databasen.

Validering: 459 tester passerar. Regressioner verifierar att badminton aldrig hämtas av standardimporten, att individuella sporter filtreras även från generiska Ticketmaster-poster, att lagsporter behålls och att kultur inte försvinner på grund av en sportreferens. Ett Streamlit AppTest verifierar huvudlistan, sportfiltret, sparade event och nollträffarnas alternativa förslag med samma begränsning.
