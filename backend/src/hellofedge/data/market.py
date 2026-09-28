"""Heures d'ouverture du marché USD/JPY (spec 0002, AC-5). Fonctions pures.

- Fermé du vendredi 17h00 au dimanche 17h00, heure de New York.
- Fermé aussi les jours fériés de `MARKET_HOLIDAYS` (dates fixes `MM-JJ`), sur toute
  la journée de New York.
- Fenêtre du rollover : de 16h58 à 17h10, heure de New York, chaque jour. Beaucoup de
  fournisseurs n'ont pas de prix pendant quelques minutes : jamais de coupure là.
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")
CLOSE_AT = time(17, 0)
ROLLOVER_START = time(16, 58)
ROLLOVER_END = time(17, 10)
FRIDAY, SUNDAY = 4, 6
# Une fermeture (week-end plus un jour férié collé) ne dure jamais plus que ça.
LONGEST_CLOSURE = timedelta(days=5)


def parse_holidays(value: str) -> frozenset[tuple[int, int]]:
    """`12-25,01-01` → {(12, 25), (1, 1)}."""
    days = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        month, day = (int(x) for x in item.split("-"))
        # Contrôle : la date doit exister (le 29 février est accepté).
        datetime(2024, month, day)
        days.add((month, day))
    return frozenset(days)


@dataclass(frozen=True)
class MarketCalendar:
    holidays: frozenset[tuple[int, int]] = frozenset()

    def is_open(self, ts: datetime) -> bool:
        ny = ts.astimezone(NEW_YORK)
        if (ny.month, ny.day) in self.holidays:
            return False
        weekday, clock = ny.weekday(), ny.time()
        if weekday == FRIDAY and clock >= CLOSE_AT:
            return False
        if weekday == 5:  # samedi
            return False
        if weekday == SUNDAY and clock < CLOSE_AT:
            return False
        return True

    @staticmethod
    def in_rollover(ts: datetime) -> bool:
        clock = ts.astimezone(NEW_YORK).time()
        return ROLLOVER_START <= clock < ROLLOVER_END

    def closed_at(self, ts: datetime) -> datetime:
        """Heure à laquelle la fermeture en cours a commencé (`ts` marché fermé).

        Recule minute par minute jusqu'à la dernière minute ouverte.
        """
        if self.is_open(ts):
            raise ValueError(f"le marché est ouvert à {ts.isoformat()}")
        cursor = ts.replace(second=0, microsecond=0)
        limit = cursor - LONGEST_CLOSURE
        while cursor > limit and not self.is_open(cursor - timedelta(minutes=1)):
            cursor -= timedelta(minutes=1)
        return cursor
