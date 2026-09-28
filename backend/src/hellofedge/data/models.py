"""Tables du module `data` (spec 0002)."""

from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from hellofedge.db import Base


class ProviderToken(Base):
    """Le dernier jeton valable d'un fournisseur (AC-13).

    Exception assumée à la règle « secrets dans l'environnement » : le jeton cTrader
    est renouvelé par le `worker` et l'ancien devient invalide, il faut donc garder le
    nouveau quelque part. Il est en lecture seule, sur un compte démo. Jamais journalisé.
    """

    __tablename__ = "provider_token"

    source: Mapped[str] = mapped_column(Text, primary_key=True)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        # Jamais le jeton lui-même, même dans une trace d'erreur.
        return f"ProviderToken(source={self.source!r}, expires_at={self.expires_at!r})"
