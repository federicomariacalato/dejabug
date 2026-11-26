IO = 1
ALTRO = 2


def bug_con_tecnologie(sql, utente_id, *nomi):
    bug_id = sql(
        "INSERT INTO bug (utente_id, titolo, errore, causa, soluzione, errore_normalizzato) "
        "VALUES (%s, 't', 'e', 'c', 's', 'e') RETURNING id",
        (utente_id,),
    )[0]["id"]
    for nome in nomi:
        tecnologia_id = sql(
            "INSERT INTO tecnologia (nome) VALUES (%s) "
            "ON CONFLICT (nome) DO UPDATE SET nome = EXCLUDED.nome RETURNING id",
            (nome,),
        )[0]["id"]
        sql("INSERT INTO bug_tecnologia (bug_id, tecnologia_id) VALUES (%s, %s)", (bug_id, tecnologia_id))


def test_livello_6_le_mie_tecnologie(client, sql):
    bug_con_tecnologie(sql, IO, "python", "git")
    bug_con_tecnologie(sql, IO, "python", "pytest")
    bug_con_tecnologie(sql, ALTRO, "java")
    risposta = client.get("/tecnologie")
    assert risposta.status_code == 200, "Manca la rotta GET /tecnologie"
    assert risposta.json() == ["git", "pytest", "python"], \
        "Solo le tecnologie dei miei bug, una volta sola, in ordine alfabetico"


def test_livello_6_nessuna_tecnologia(client, sql):
    bug_con_tecnologie(sql, ALTRO, "java")
    risposta = client.get("/tecnologie")
    assert risposta.status_code == 200, "Manca la rotta GET /tecnologie"
    assert risposta.json() == [], "Senza bug miei, nessuna tecnologia"


def test_livello_6_autocompletamento(client, sql):
    bug_con_tecnologie(sql, IO, "python", "pytest", "git", "pip")
    bug_con_tecnologie(sql, ALTRO, "pyspark")
    risposta = client.get("/tecnologie", params={"inizio": "py"})
    assert risposta.json() == ["pytest", "python"], \
        "?inizio=py dà le mie tecnologie che iniziano con py"


def test_livello_6_autocompletamento_maiuscole(client, sql):
    bug_con_tecnologie(sql, IO, "python", "git")
    risposta = client.get("/tecnologie", params={"inizio": "PY"})
    assert risposta.json() == ["python"], "?inizio=PY vale come ?inizio=py"
