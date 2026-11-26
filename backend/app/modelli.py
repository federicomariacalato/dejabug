from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UtenteDB(Base):
    __tablename__ = "utente"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    nome: Mapped[str]
    password_hash: Mapped[str]
    creato_il: Mapped[datetime] = mapped_column(server_default=func.now())
