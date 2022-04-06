Organizarea
Am lucrat tema foarte indeaproape de scheletul oferit (am adus foarte mici
modificari; spre exemplu, am adaugat clasa atomicInteger si variabile statice
pentru pozitia semaforului si a listei de produse pentru un producator)

Tema mi-a placut. Cu siguranta mi-am imbunatatit modul de lucru cu Python.
Am imbinat cunostintele din primele laboratoare de ASC impreuna cu ceea ce
am invatat la APD. 

Implementarea mea o consider eficienta. Totusi, am pus valorile la timeout
ca parametru pentru acquire destul de empiric, cat sa nu afecteze mult
timpul de rulare al testelor.

Implementare
Am facut tema in totalitate, impreuna cu unit testing si logging.
Tema nu mi s-a parut dificila. Mi-a luat ca timp sa inteleg
scheletul 1 ora jumate - 2 ore. Dupa aceea, lucrurile au mers
destul de natural.
Problema pe care am avut-o a fost legata de producatori si
consumatorii care scoteau lucruri din cos, pentru ca in momentul
respectiv, eu consideram ca producatorul poate produce din nou
si am avut ceva probleme cu asta (marind cumva capacitatea
de productie a capacitorului dincolo de limita specificata
in constructorul marketplace-ului). Astfel, am luat decizia
ca producatorul sa nu poate produce pana se plaseaza o comanda
care practic ii da din nou libertatea de a produce.
