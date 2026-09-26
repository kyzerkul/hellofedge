"""Points de référence OANDA lus sur les captures du trader (`exemples/reference_oanda.csv`).

Deux types de points (spec 0002, *Points de référence*) :
- `exact` : une valeur qui ne bouge plus (open de la bougie en cours, extrême étiqueté
  d'une bougie terminée) ;
- `borne` : le H ou le L de la bougie en cours, qui n'est qu'une limite du vrai H ou L.
"""

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path

from hellofedge.data.candle import check_utc_minute
from hellofedge.data.timeframes import bucket_start

COLUMNS = ["capture", "ut", "type", "ts_open_utc", "prix", "champ", "note"]
UNITS = (1, 3, 5)
FIELDS = ("open", "high", "low", "close")


class PointType(StrEnum):
    EXACT = "exact"
    BORNE = "borne"


@dataclass(frozen=True, slots=True)
class ReferencePoint:
    capture: str
    ut: int
    type: PointType
    ts_open: datetime
    prix: Decimal
    champ: str
    note: str


class ReferenceFileError(ValueError):
    """Le fichier de référence ne respecte pas le format de la spec 0002."""


def load_reference(path: Path) -> list[ReferencePoint]:
    """Lit et contrôle le fichier. Toute ligne invalide arrête la lecture avec son numéro."""
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            raise ReferenceFileError(
                f"colonnes attendues {COLUMNS}, trouvées {reader.fieldnames}"
            )
        points = []
        for line, row in enumerate(reader, start=2):
            try:
                points.append(_parse(row))
            except (ValueError, InvalidOperation) as exc:
                raise ReferenceFileError(f"{path.name}, ligne {line} : {exc}") from exc
    return points


def _parse(row: dict[str, str]) -> ReferencePoint:
    ut = int(row["ut"])
    if ut not in UNITS:
        raise ValueError(f"ut doit valoir 1, 3 ou 5, pas {ut}")
    ts = datetime.fromisoformat(row["ts_open_utc"])
    check_utc_minute(ts)
    if bucket_start(ts, ut) != ts:
        raise ValueError(f"{ts:%H:%M} ne tombe pas sur une bougie M{ut}")
    prix = Decimal(row["prix"])
    if prix.as_tuple().exponent != -3:
        raise ValueError(f"prix attendu avec 3 décimales, pas {row['prix']}")
    champ = row["champ"]
    if champ not in FIELDS:
        raise ValueError(f"champ inconnu : {champ}")
    point_type = PointType(row["type"])
    if point_type is PointType.BORNE and champ not in ("high", "low"):
        raise ValueError("une borne porte sur high ou low")
    if not row["capture"]:
        raise ValueError("capture vide")
    return ReferencePoint(
        capture=row["capture"],
        ut=ut,
        type=point_type,
        ts_open=ts,
        prix=prix,
        champ=champ,
        note=row["note"],
    )
