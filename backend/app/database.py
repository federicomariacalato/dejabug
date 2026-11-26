from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Impostazioni(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / ".env", extra="ignore")

    database_url: str


impostazioni = Impostazioni()

engine = create_engine(impostazioni.database_url)


class Base(DeclarativeBase):
    pass


def get_db():
    with Session(engine) as db:
        yield db
