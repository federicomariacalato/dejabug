<!-- CANVAS.md · Il canvas del capitolo 1: l'app in una pagina. -->
<!-- Chi apre la cartella capisce cos'è. -->

# DejaBug · il diario dei bug

**In una frase:** DejaBug ti fa ritrovare in pochi secondi la soluzione degli errori che hai già risolto e ti mostra quali ripeti più spesso.

## Problema
Chi impara a programmare rincontra errori già risolti, ma non ne ricorda più causa e soluzione: gli appunti sono sparsi tra note, chat e file e non si possono cercare. Così rifà da capo la stessa ricerca e non sa quali errori ripete.

## Utente
Uno studente di coding (corso, bootcamp, autodidatta) o uno sviluppatore junior, che incontra molti errori ogni giorno e ritrova spesso quelli già visti.

## MVP
- Registrazione, login e cancellazione dell'account (reinserendo la password)
- Registrare un bug, modificarlo e cancellarlo: errore, causa, soluzione e almeno una tecnologia obbligatori; titolo proposto dall'ultima riga dell'errore; minuti persi scelti tra 5, 15, 30, 60, 120+
- Tecnologie (git, python, java...) in minuscolo, con autocompletamento da quelle già usate
- Ricerca per somiglianza: incolli un errore e trovi quelli simili già risolti, anche se percorsi e numeri di riga sono diversi
- Pulsante "Mi è ricapitato" per registrare una ripetizione, con un commento facoltativo
- Statistiche: errori ripetuti e minuti persi per settimana
- Piccola CLI per cercare dal terminale: `dejabug cerca "<errore>"`

## Fuori dall'MVP
Bug pubblici e commenti, esportazione, filtro e grafico per tecnologia, suggerimenti con l'AI, login con Google o GitHub, app mobile, responsive completo.

## Stack
FastAPI (backend) · PostgreSQL con `pg_trgm` (database e ricerca) · React (interfaccia web) · Python (CLI)

## Database
Le tabelle sono in [`schema.sql`](schema.sql):
- `utente`: chi usa l'app
- `bug`: la scheda di un errore (errore, causa, soluzione, più l'errore normalizzato per la ricerca)
- `tecnologia`: git, python, java..., condivise tra tutti
- `bug_tecnologia`: quali tecnologie ha ogni bug
- `ripetizione`: ogni volta che un bug capita, con minuti persi e commento

## Come lo costruisco
Metodo agile, un incremento funzionante alla volta:
schema → API → ricerca → login → deploy → React → CLI

## Sicurezza
Password salvate solo come hash (argon2) · token JWT che scade dopo qualche ora · ogni utente vede e modifica solo i propri bug · segreti nel file `.env`, mai su GitHub.
