# Incremento 1 · le API dei bug

Le rotte per registrare, leggere, modificare e cancellare i bug, più "Mi è ricapitato" e l'autocompletamento delle tecnologie. Per ora niente login: l'utente corrente è sempre l'utente 1.

## I file

| File | Cosa c'è | Si tocca? |
|---|---|---|
| `schema.sql` | Le cinque tabelle | No |
| `app/database.py` | `engine`, `Base`, `get_db`: legge `DATABASE_URL` dal `.env` | No |
| `app/modelli.py` | `UtenteDB` è già scritto, da esempio. `BugDB`, `TecnologiaDB`, `BugTecnologiaDB`, `RipetizioneDB` li scrivi tu | **Sì** |
| `app/schemi.py` | Vuoto: gli stampi Pydantic | **Sì** |
| `app/dipendenze.py` | Vuoto: `utente_corrente` | **Sì** |
| `app/rotte/bug.py` | Solo `router = APIRouter()`: le rotte dei bug | **Sì** |
| `app/rotte/tecnologie.py` | Solo `router = APIRouter()`: l'autocompletamento | **Sì** |
| `app/main.py` | Solo `app = FastAPI(...)`: `/salute` e i due router | **Sì** |
| `tests/` | I test dei livelli, sul database `dejabug_test` | No |

## Livello 0 · Una volta sola

Dalla cartella `backend`. Il `.venv` di adesso è stato creato quando il progetto stava in un'altra cartella e i suoi comandi non partono più: va rifatto.

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
createdb dejabug
psql -d dejabug -f schema.sql
createdb dejabug_test
```

Poi scrivi nel file `.env`:

```
DATABASE_URL=postgresql+psycopg:///dejabug
```

I test non toccano `dejabug`: prima di ogni test cancellano e rifanno da capo `dejabug_test` con `schema.sql`, con due utenti dentro (1 sei tu, 2 è un altro).

Un livello alla volta: `pytest -v -k livello_0`. Se un test è rosso, leggi l'ultima riga del messaggio.

**Livello 0.** `GET /salute` risponde `{"stato": "ok"}`.

## Livello 1 · POST /bug

- Scrivi i quattro modelli in `modelli.py`, guardando `schema.sql`. Due aiuti:
  - le colonne facoltative sono `Mapped[int | None]`;
  - le chiavi esterne sono `mapped_column(ForeignKey("bug.id"))`.
- Scrivi `utente_corrente` in `dipendenze.py`: per ora restituisce `1`. Ogni rotta la usa con `Depends`.

**Cosa riceve.** `errore`, `causa`, `soluzione` e `tecnologie` sono obbligatori; `titolo` e `minuti_persi` sono facoltativi.

```json
{
  "titolo": "Manca numpy",
  "errore": "Traceback...\nModuleNotFoundError: No module named 'numpy'",
  "causa": "Il venv non era attivo",
  "soluzione": "source .venv/bin/activate",
  "tecnologie": ["Python", "pip"],
  "minuti_persi": 30
}
```

**Cosa risponde:** `201`, con il bug.

```json
{"id": 1, "titolo": "...", "errore": "...", "causa": "...", "soluzione": "...", "tecnologie": ["pip", "python"], "ripetizioni": 1}
```

**Le regole:**
- Un campo vuoto, o fatto solo di spazi, vale come mancante e dà `422`. Aiuto: `Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]`.
- Serve almeno una tecnologia (`Field(min_length=1)`), e nessuna può essere vuota.
- Le tecnologie si salvano in minuscolo e senza duplicati: Git, git e GIT sono una sola. Se una tecnologia esiste già nella tabella `tecnologia`, si riusa quella.
- Il titolo scritto dall'utente ha al massimo 80 caratteri. Se il titolo è vuoto, si usa l'ultima riga non vuota dell'errore (senza spazi ai lati), tagliata a 80 caratteri.
- `errore_normalizzato` è quella stessa ultima riga, in minuscolo. La versione completa, che toglie percorsi e numeri, arriverà con la ricerca.
- `minuti_persi` è uno tra 5, 15, 30, 60 e 120, oppure manca. Aiuto: `Literal[5, 15, 30, 60, 120] | None`.
- Insieme al bug si crea la sua prima ripetizione, con i `minuti_persi`.

## Livello 2 · GET /bug e GET /bug/{bug_id}

- `GET /bug` restituisce i bug dell'utente corrente, dal più recente, nella stessa forma della risposta del livello 1.
- `GET /bug/{bug_id}` restituisce un bug solo. `ripetizioni` è il numero di ripetizioni di quel bug.
- Se il bug non esiste, oppure è di un altro utente, la risposta è `404`.

## Livello 3 · PUT /bug/{bug_id}

- Riceve gli stessi campi della creazione, tranne `minuti_persi`, con le stesse regole.
- Le tecnologie nuove sostituiscono le vecchie.
- `errore_normalizzato` si ricalcola, e `modificato_il` diventa l'ora della modifica.
- Le ripetizioni non cambiano.
- Risponde `200` con il bug. Se il bug non esiste o è di un altro, `404`.

## Livello 4 · DELETE /bug/{bug_id}

- Risponde `204`. Le ripetizioni e i collegamenti alle tecnologie se ne vanno da soli (`ON DELETE CASCADE`).
- Le tecnologie restano, perché sono condivise.
- Se il bug non esiste o è di un altro, `404`.

## Livello 5 · POST /bug/{bug_id}/ripetizioni

È il pulsante "Mi è ricapitato".

**Cosa riceve:** `{"minuti_persi": 15, "commento": "di nuovo!"}`. Entrambi i campi sono facoltativi, e `{}` va bene.

**Cosa risponde:** `201`, con la ripetizione: `{"id": 2, "data": "...", "minuti_persi": 15, "commento": "di nuovo!"}`.

Se il bug non esiste o è di un altro, `404`.

## Livello 6 · GET /tecnologie

- `GET /tecnologie` restituisce le tecnologie dei bug dell'utente corrente: nomi, una volta sola, in ordine alfabetico.
- `GET /tecnologie?inizio=py` restituisce solo quelle che iniziano con `py`. `?inizio=PY` vale come `?inizio=py`.
