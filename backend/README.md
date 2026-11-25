<!-- README.md · Come si avvia il progetto. -->
<!-- In cinque righe. -->

# DejaBug · backend

Il diario dei bug: ritrova in pochi secondi la soluzione degli errori che hai già risolto.

Serve **Python 3.13** (controlla con `python3 --version`) e un database PostgreSQL.

1. Crea l'ambiente: `python3 -m venv .venv && source .venv/bin/activate`
2. Installa le librerie: `pip install -r requirements.txt`
3. Copia le impostazioni: `cp .env.example .env` e scrivi in `.env` i valori veri
4. Crea le tabelle eseguendo `schema.sql` sul tuo database PostgreSQL
5. Avvia l'API: `fastapi dev app/main.py` (documentazione su http://127.0.0.1:8000/docs) · test: `pytest`
