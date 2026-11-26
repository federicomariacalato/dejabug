def test_livello_0_salute(client):
    risposta = client.get("/salute")
    assert risposta.status_code == 200, "Manca la rotta GET /salute"
    assert risposta.json() == {"stato": "ok"}, 'GET /salute risponde con {"stato": "ok"}'
