import pytest

IO = 1
ALTRO = 2

ERRORE_NUMPY = (
    "Traceback (most recent call last):\n"
    '  File "/home/io/progetto/main.py", line 3, in <module>\n'
    "    import numpy\n"
    "ModuleNotFoundError: No module named 'numpy'"
)

NUOVO = {
    "errore": ERRORE_NUMPY,
    "causa": "Il venv non era attivo",
    "soluzione": "source .venv/bin/activate",
    "tecnologie": ["Python", "pip"],
}


def crea(client, **campi):
    risposta = client.post("/bug", json={**NUOVO, **campi})
    assert risposta.status_code == 201, "POST /bug risponde 201 (Created): status_code=201 nella rotta"
    return risposta.json()


def bug_nel_database(sql, utente_id=IO, titolo="Manca numpy", errore=ERRORE_NUMPY,
                     tecnologie=("python",), ripetizioni=1) -> int:
    bug_id = sql(
        "INSERT INTO bug (utente_id, titolo, errore, causa, soluzione, errore_normalizzato) "
        "VALUES (%s, %s, %s, 'una causa', 'una soluzione', lower(%s)) RETURNING id",
        (utente_id, titolo, errore, errore),
    )[0]["id"]
    for nome in tecnologie:
        tecnologia_id = sql(
            "INSERT INTO tecnologia (nome) VALUES (%s) "
            "ON CONFLICT (nome) DO UPDATE SET nome = EXCLUDED.nome RETURNING id",
            (nome,),
        )[0]["id"]
        sql("INSERT INTO bug_tecnologia (bug_id, tecnologia_id) VALUES (%s, %s)", (bug_id, tecnologia_id))
    for _ in range(ripetizioni):
        sql("INSERT INTO ripetizione (bug_id) VALUES (%s)", (bug_id,))
    return bug_id


def test_livello_1_crea_un_bug(client, sql):
    risposta = client.post("/bug", json=NUOVO)
    assert risposta.status_code == 201, "POST /bug risponde 201 (Created): status_code=201 nella rotta"
    bug = risposta.json()
    assert isinstance(bug.get("id"), int), "La risposta contiene l'id del bug"
    assert bug["errore"] == ERRORE_NUMPY, "L'errore si salva così com'è"
    assert bug["causa"] == NUOVO["causa"]
    assert bug["soluzione"] == NUOVO["soluzione"]
    assert sorted(bug["tecnologie"]) == ["pip", "python"], "tecnologie è una lista di nomi, in minuscolo"
    assert bug["ripetizioni"] == 1, "Un bug appena creato ha già una ripetizione: la prima volta"

    righe = sql("SELECT utente_id FROM bug WHERE id = %s", (bug["id"],))
    assert righe, "Il bug non è nel database: manca db.commit()?"
    assert righe[0]["utente_id"] == IO, "Il bug è dell'utente corrente (utente_corrente)"


def test_livello_1_titolo_dall_ultima_riga(client):
    bug = crea(client)
    assert bug["titolo"] == "ModuleNotFoundError: No module named 'numpy'", \
        "Senza titolo, il titolo è l'ultima riga dell'errore"


def test_livello_1_titolo_ignora_le_righe_vuote_in_fondo(client):
    bug = crea(client, errore=ERRORE_NUMPY + "\n\n  \n")
    assert bug["titolo"] == "ModuleNotFoundError: No module named 'numpy'", \
        "L'ultima riga è l'ultima che non è vuota (e senza spazi ai lati)"


def test_livello_1_titolo_vuoto_come_assente(client):
    bug = crea(client, titolo="   ")
    assert bug["titolo"] == "ModuleNotFoundError: No module named 'numpy'", \
        "Un titolo fatto solo di spazi vale come nessun titolo"


def test_livello_1_titolo_scelto(client):
    bug = crea(client, titolo="Manca numpy")
    assert bug["titolo"] == "Manca numpy", "Se l'utente scrive il titolo, resta il suo"


def test_livello_1_titolo_automatico_tagliato_a_80(client):
    riga = "E" * 100
    bug = crea(client, errore=riga)
    assert bug["titolo"] == riga[:80], "Il titolo automatico si taglia a 80 caratteri"


def test_livello_1_titolo_scelto_troppo_lungo(client):
    risposta = client.post("/bug", json={**NUOVO, "titolo": "T" * 81})
    assert risposta.status_code == 422, "Un titolo scritto dall'utente ha al massimo 80 caratteri"


@pytest.mark.parametrize("campo", ["errore", "causa", "soluzione"])
def test_livello_1_campo_obbligatorio_mancante(client, campo):
    senza = {k: v for k, v in NUOVO.items() if k != campo}
    assert client.post("/bug", json=senza).status_code == 422, f"{campo} è obbligatorio"


@pytest.mark.parametrize("campo", ["errore", "causa", "soluzione"])
def test_livello_1_campo_obbligatorio_solo_spazi(client, campo):
    risposta = client.post("/bug", json={**NUOVO, campo: "   "})
    assert risposta.status_code == 422, f"{campo} fatto solo di spazi vale come vuoto: 422"


@pytest.mark.parametrize("tecnologie", [None, [], ["   "]])
def test_livello_1_almeno_una_tecnologia(client, tecnologie):
    corpo = {k: v for k, v in NUOVO.items() if k != "tecnologie"}
    if tecnologie is not None:
        corpo["tecnologie"] = tecnologie
    assert client.post("/bug", json=corpo).status_code == 422, \
        "Serve almeno una tecnologia, e una tecnologia non può essere vuota"


def test_livello_1_tecnologie_minuscole_e_condivise(client, sql):
    crea(client, tecnologie=["Git"])
    bug = crea(client, tecnologie=["git", " GIT "])
    assert bug["tecnologie"] == ["git"], "Git, git e GIT sono la stessa tecnologia, una volta sola"
    righe = sql("SELECT nome FROM tecnologia")
    assert [r["nome"] for r in righe] == ["git"], \
        "Una tecnologia che esiste già si riusa: nella tabella tecnologia c'è una riga sola"


def test_livello_1_errore_normalizzato(client, sql):
    bug = crea(client, errore=ERRORE_NUMPY + "\n")
    riga = sql("SELECT errore_normalizzato FROM bug WHERE id = %s", (bug["id"],))[0]
    assert riga["errore_normalizzato"] == "modulenotfounderror: no module named 'numpy'", \
        "errore_normalizzato è l'ultima riga non vuota dell'errore, in minuscolo"


def test_livello_1_prima_ripetizione_con_minuti(client, sql):
    bug = crea(client, minuti_persi=30)
    righe = sql("SELECT minuti_persi FROM ripetizione WHERE bug_id = %s", (bug["id"],))
    assert len(righe) == 1, "Creando il bug si crea anche la sua prima ripetizione"
    assert righe[0]["minuti_persi"] == 30, "minuti_persi va nella prima ripetizione"


def test_livello_1_prima_ripetizione_senza_minuti(client, sql):
    bug = crea(client)
    righe = sql("SELECT minuti_persi FROM ripetizione WHERE bug_id = %s", (bug["id"],))
    assert len(righe) == 1, "Creando il bug si crea anche la sua prima ripetizione"
    assert righe[0]["minuti_persi"] is None, "minuti_persi è facoltativo"


@pytest.mark.parametrize("minuti", [0, 7, 121])
def test_livello_1_minuti_fissi(client, minuti):
    risposta = client.post("/bug", json={**NUOVO, "minuti_persi": minuti})
    assert risposta.status_code == 422, "minuti_persi è uno tra 5, 15, 30, 60, 120"


def test_livello_2_i_miei_bug(client, sql):
    primo = bug_nel_database(sql, titolo="Primo")
    bug_nel_database(sql, utente_id=ALTRO, titolo="Di un altro")
    secondo = bug_nel_database(sql, titolo="Secondo")
    risposta = client.get("/bug")
    assert risposta.status_code == 200, "Manca la rotta GET /bug"
    bugs = risposta.json()
    assert [b["titolo"] for b in bugs] == ["Secondo", "Primo"], \
        "GET /bug dà solo i bug dell'utente corrente, dal più recente"
    assert [b["id"] for b in bugs] == [secondo, primo]


def test_livello_2_nessun_bug(client):
    risposta = client.get("/bug")
    assert risposta.status_code == 200, "Manca la rotta GET /bug"
    assert risposta.json() == [], "Senza bug, GET /bug dà una lista vuota"


def test_livello_2_un_bug(client, sql):
    bug_id = bug_nel_database(sql, tecnologie=("python", "pip"), ripetizioni=3)
    risposta = client.get(f"/bug/{bug_id}")
    assert risposta.status_code == 200, "Manca la rotta GET /bug/{bug_id}"
    bug = risposta.json()
    assert bug["id"] == bug_id
    assert bug["titolo"] == "Manca numpy"
    assert bug["errore"] == ERRORE_NUMPY
    assert bug["causa"] == "una causa"
    assert bug["soluzione"] == "una soluzione"
    assert sorted(bug["tecnologie"]) == ["pip", "python"]
    assert bug["ripetizioni"] == 3, "ripetizioni è il numero di righe nella tabella ripetizione"


def test_livello_2_bug_che_non_esiste(client):
    assert client.get("/bug/999").status_code == 404, "Un bug che non esiste: 404"


def test_livello_2_bug_di_un_altro(client, sql):
    bug_id = bug_nel_database(sql, utente_id=ALTRO)
    assert client.get(f"/bug/{bug_id}").status_code == 404, \
        "Il bug di un altro utente non si vede: 404, come se non esistesse"


MODIFICA = {
    "titolo": "Manca requests",
    "errore": "ModuleNotFoundError: No module named 'requests'",
    "causa": "Non l'avevo installato",
    "soluzione": "pip install requests",
    "tecnologie": ["Pip"],
}


def test_livello_3_modifica_un_bug(client, sql):
    bug_id = bug_nel_database(sql, tecnologie=("python",), ripetizioni=2)
    risposta = client.put(f"/bug/{bug_id}", json=MODIFICA)
    assert risposta.status_code == 200, "Manca la rotta PUT /bug/{bug_id}"
    bug = risposta.json()
    assert bug["id"] == bug_id
    assert bug["titolo"] == "Manca requests"
    assert bug["errore"] == MODIFICA["errore"]
    assert bug["causa"] == MODIFICA["causa"]
    assert bug["soluzione"] == MODIFICA["soluzione"]
    assert bug["tecnologie"] == ["pip"], "Le tecnologie si sostituiscono: quelle vecchie spariscono"
    assert bug["ripetizioni"] == 2, "Modificare un bug non tocca le ripetizioni"

    riga = sql("SELECT * FROM bug WHERE id = %s", (bug_id,))[0]
    assert riga["errore"] == MODIFICA["errore"], "La modifica non è nel database: manca db.commit()?"
    assert riga["errore_normalizzato"] == "modulenotfounderror: no module named 'requests'", \
        "Se cambia l'errore, si ricalcola errore_normalizzato"
    assert riga["modificato_il"] > riga["creato_il"], "modificato_il diventa l'ora della modifica"


def test_livello_3_titolo_vuoto_si_ricalcola(client, sql):
    bug_id = bug_nel_database(sql)
    risposta = client.put(f"/bug/{bug_id}", json={**MODIFICA, "titolo": ""})
    assert risposta.status_code == 200, "Manca la rotta PUT /bug/{bug_id}"
    bug = risposta.json()
    assert bug["titolo"] == "ModuleNotFoundError: No module named 'requests'", \
        "Anche nella modifica, senza titolo si usa l'ultima riga dell'errore"


def test_livello_3_stesse_regole_della_creazione(client, sql):
    bug_id = bug_nel_database(sql)
    risposta = client.put(f"/bug/{bug_id}", json={**MODIFICA, "tecnologie": []})
    assert risposta.status_code == 422, "La modifica ha le stesse regole della creazione"
    risposta = client.put(f"/bug/{bug_id}", json={**MODIFICA, "causa": " "})
    assert risposta.status_code == 422, "La modifica ha le stesse regole della creazione"


def test_livello_3_bug_che_non_esiste(client):
    assert client.put("/bug/999", json=MODIFICA).status_code == 404, "Un bug che non esiste: 404"


def test_livello_3_bug_di_un_altro(client, sql):
    bug_id = bug_nel_database(sql, utente_id=ALTRO)
    assert client.put(f"/bug/{bug_id}", json=MODIFICA).status_code == 404, \
        "Il bug di un altro utente non si modifica: 404"
    riga = sql("SELECT titolo FROM bug WHERE id = %s", (bug_id,))[0]
    assert riga["titolo"] == "Manca numpy", "Il bug dell'altro utente è rimasto com'era"


def test_livello_4_cancella_un_bug(client, sql):
    bug_id = bug_nel_database(sql, tecnologie=("python",), ripetizioni=2)
    risposta = client.delete(f"/bug/{bug_id}")
    assert risposta.status_code == 204, "DELETE /bug/{bug_id} risponde 204 (No Content)"
    assert client.get(f"/bug/{bug_id}").status_code == 404, "Dopo la cancellazione il bug non c'è più"
    assert sql("SELECT * FROM bug WHERE id = %s", (bug_id,)) == [], \
        "Il bug è ancora nel database: manca db.commit()?"
    assert sql("SELECT * FROM ripetizione") == [], "Con il bug se ne vanno le sue ripetizioni"
    assert sql("SELECT * FROM bug_tecnologia") == [], "Con il bug se ne vanno i suoi collegamenti"
    assert [r["nome"] for r in sql("SELECT nome FROM tecnologia")] == ["python"], \
        "La tecnologia resta: è condivisa tra tutti"


def test_livello_4_bug_che_non_esiste(client):
    assert client.delete("/bug/999").status_code == 404, "Un bug che non esiste: 404"


def test_livello_4_bug_di_un_altro(client, sql):
    bug_id = bug_nel_database(sql, utente_id=ALTRO)
    assert client.delete(f"/bug/{bug_id}").status_code == 404, \
        "Il bug di un altro utente non si cancella: 404"
    assert sql("SELECT id FROM bug WHERE id = %s", (bug_id,)), "Il bug dell'altro utente è ancora lì"


def test_livello_5_mi_e_ricapitato(client, sql):
    bug_id = bug_nel_database(sql)
    risposta = client.post(f"/bug/{bug_id}/ripetizioni", json={"minuti_persi": 15, "commento": "di nuovo!"})
    assert risposta.status_code == 201, "Manca la rotta POST /bug/{bug_id}/ripetizioni (risponde 201)"
    ripetizione = risposta.json()
    assert isinstance(ripetizione.get("id"), int), "La risposta contiene l'id della ripetizione"
    assert ripetizione["minuti_persi"] == 15
    assert ripetizione["commento"] == "di nuovo!"
    assert ripetizione.get("data"), "La risposta contiene la data della ripetizione"
    assert sql("SELECT count(*) AS n FROM ripetizione WHERE bug_id = %s", (bug_id,))[0]["n"] == 2, \
        "Ora il bug ha due ripetizioni: manca db.commit()?"


def test_livello_5_tutto_facoltativo(client, sql):
    bug_id = bug_nel_database(sql)
    risposta = client.post(f"/bug/{bug_id}/ripetizioni", json={})
    assert risposta.status_code == 201, "Minuti e commento sono facoltativi"
    ripetizione = risposta.json()
    assert ripetizione["minuti_persi"] is None
    assert ripetizione["commento"] is None


def test_livello_5_minuti_fissi(client, sql):
    bug_id = bug_nel_database(sql)
    risposta = client.post(f"/bug/{bug_id}/ripetizioni", json={"minuti_persi": 7})
    assert risposta.status_code == 422, "minuti_persi è uno tra 5, 15, 30, 60, 120"


def test_livello_5_bug_che_non_esiste(client):
    assert client.post("/bug/999/ripetizioni", json={}).status_code == 404, "Un bug che non esiste: 404"


def test_livello_5_bug_di_un_altro(client, sql):
    bug_id = bug_nel_database(sql, utente_id=ALTRO)
    assert client.post(f"/bug/{bug_id}/ripetizioni", json={}).status_code == 404, \
        "Sul bug di un altro utente non si aggiungono ripetizioni: 404"
    assert len(sql("SELECT * FROM ripetizione WHERE bug_id = %s", (bug_id,))) == 1, \
        "Il bug dell'altro utente ha ancora una ripetizione sola"
