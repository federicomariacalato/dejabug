import os
from pathlib import Path

NOME_DB_TEST = os.environ.get("DEJABUG_DB_TEST", "dejabug_test")
os.environ["DATABASE_URL"] = f"postgresql+psycopg:///{NOME_DB_TEST}"

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from app.main import app

SCHEMA = (Path(__file__).parent.parent / "schema.sql").read_text()


@pytest.fixture(autouse=True)
def database_come_nuovo():
    with psycopg.connect(dbname=NOME_DB_TEST) as conn:
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")
        conn.execute(SCHEMA)
        conn.execute(
            "INSERT INTO utente (email, nome, password_hash) VALUES "
            "('io@dejabug.test', 'Io', 'x'), ('altro@dejabug.test', 'Altro', 'x')"
        )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sql():
    def esegui(query, valori=None):
        with psycopg.connect(dbname=NOME_DB_TEST, row_factory=dict_row) as conn:
            cur = conn.execute(query, valori)
            return cur.fetchall() if cur.description else []

    return esegui
