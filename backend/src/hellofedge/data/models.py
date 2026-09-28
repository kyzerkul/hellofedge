"""Tables du module `data` (spec 0002).

Les prix sont en NUMERIC(10,3), jamais en nombre à virgule flottante : 0,2 pip doit
rester exactement 0,002. Toutes les heures sont en UTC.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    Numeric,
    Text,
    false,
    text,
)
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


PRICE = Numeric(10, 3)

OUTAGE_CAUSES = (
    "timeout",
    "erreur_api",
    "reseau",
    "auth",
    "limite_api",
    "donnees_absentes",
)
OUTAGE_CLOSED_REASONS = ("retour_flux", "fermeture_marche")
REVISED_FIELDS = ("open", "high", "low", "close")


def _one_of(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class CandleM1(Base):
    """Une bougie M1 bid d'une source : la seule vérité en base.

    Jamais réécrite ni supprimée par le code applicatif (AC-10). Les autres UT sont
    recalculées depuis cette table, jamais stockées.
    """

    __tablename__ = "candle_m1"
    __table_args__ = (
        CheckConstraint(
            "date_trunc('minute', ts_open) = ts_open", name="minute_pleine"
        ),
        CheckConstraint(
            "low <= least(open, close) AND high >= greatest(open, close)",
            name="ohlc_coherent",
        ),
    )

    source: Mapped[str] = mapped_column(Text, primary_key=True)
    ts_open: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[Decimal] = mapped_column(PRICE)
    high: Mapped[Decimal] = mapped_column(PRICE)
    low: Mapped[Decimal] = mapped_column(PRICE)
    close: Mapped[Decimal] = mapped_column(PRICE)
    ask_close: Mapped[Decimal | None] = mapped_column(PRICE)
    tick_volume: Mapped[int | None] = mapped_column(Integer)
    backfilled: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FeedOutage(Base):
    """Une coupure de la source. Au plus une coupure ouverte par source."""

    __tablename__ = "feed_outage"
    __table_args__ = (
        CheckConstraint(_one_of("cause", OUTAGE_CAUSES), name="cause"),
        CheckConstraint(
            "closed_reason IS NULL OR "
            + _one_of("closed_reason", OUTAGE_CLOSED_REASONS),
            name="closed_reason",
        ),
        CheckConstraint(
            "(ended_at IS NULL) = (closed_reason IS NULL)", name="fermeture_complete"
        ),
        Index(
            "uq_feed_outage_source_ouverte",
            "source",
            unique=True,
            postgresql_where=text("ended_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    source: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cause: Mapped[str] = mapped_column(Text)
    closed_reason: Mapped[str | None] = mapped_column(Text)
    bars_backfilled: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0")
    )


class CandleRevision(Base):
    """Une valeur différente renvoyée plus tard pour une bougie déjà stockée (AC-10).

    La bougie stockée reste celle que le moteur a vue ; seule la différence est notée.
    """

    __tablename__ = "candle_revision"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source", "ts_open"], ["candle_m1.source", "candle_m1.ts_open"]
        ),
        CheckConstraint(_one_of("champ", REVISED_FIELDS), name="champ"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    source: Mapped[str] = mapped_column(Text)
    ts_open: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    champ: Mapped[str] = mapped_column(Text)
    valeur_stockee: Mapped[Decimal] = mapped_column(PRICE)
    valeur_recue: Mapped[Decimal] = mapped_column(PRICE)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
