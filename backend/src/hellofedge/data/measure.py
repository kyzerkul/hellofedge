"""Mesure d'une source contre les points OANDA (spec 0002, AC-2, AC-7, AC-12).

- `score` compare chaque point de référence à la bougie de la source (M1, ou M3 et M5
  reconstruits depuis le M1), et aussi aux bougies voisines (une période avant et
  après) pour révéler un décalage d'une minute.
- `oldest_candle` cherche la plus ancienne bougie M1 fournie (profondeur d'historique).
- `render_compare` et `render_live` écrivent chacune leur section du rapport
  `exemples/mesure_sources.md` ; `write_section` remplace une section sans toucher
  à l'autre.

Calcul de l'écart : pour un point `exact`, |prix de la source − prix de référence|.
Pour une `borne`, 0 si la source respecte la borne, sinon le dépassement.
"""

import re
import statistics
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from hellofedge.data.candle import M1, Candle
from hellofedge.data.feed import FeedError, PriceFeed
from hellofedge.data.reference import PointType, ReferencePoint
from hellofedge.data.timeframes import aggregate

# Seuil « assez proche » décidé dans la spec : 0,3 pip.
THRESHOLD = Decimal("0.003")
# Part des points sous le seuil attendue pour dire que la source est proche d'OANDA.
TARGET_SHARE = 0.90
# Marge de bougies M1 demandées autour des points d'une journée.
MARGIN = timedelta(minutes=15)
# Profondeur cherchée : 2 ans.
HORIZON = timedelta(days=730)


def point_error(point: ReferencePoint, candle: Candle) -> Decimal:
    value: Decimal = getattr(candle, point.champ)
    if point.type is PointType.EXACT:
        return abs(value - point.prix)
    if point.champ == "high":
        # Le vrai plus haut final est au moins égal au H lu.
        return max(Decimal(0), point.prix - value)
    # Le vrai plus bas final est au plus égal au L lu.
    return max(Decimal(0), value - point.prix)


@dataclass(frozen=True)
class PointResult:
    point: ReferencePoint
    source_value: Decimal | None
    error: Decimal | None
    # Écart avec la bougie d'une période avant (-1) et après (+1), si elle existe.
    neighbours: dict[int, Decimal | None] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is not None and self.error <= THRESHOLD

    @property
    def shift_hint(self) -> int | None:
        """-1 ou +1 si la bougie voisine colle au point alors que la bonne bougie non."""
        if self.ok:
            return None
        for offset in (-1, 1):
            err = self.neighbours.get(offset)
            if err is not None and err <= THRESHOLD:
                return offset
        return None


def score(points: Sequence[ReferencePoint], m1: Sequence[Candle]) -> list[PointResult]:
    """Compare chaque point à la bougie de la source de même heure et même UT."""
    by_ut: dict[int, dict[datetime, Candle]] = {}
    for ut in sorted({p.ut for p in points}):
        by_ut[ut] = {c.ts_open: c for c in aggregate(m1, ut)}
    results = []
    for p in points:
        candles = by_ut[p.ut]
        main = candles.get(p.ts_open)
        neighbours = {}
        for offset in (-1, 1):
            other = candles.get(p.ts_open + offset * p.ut * M1)
            neighbours[offset] = None if other is None else point_error(p, other)
        results.append(
            PointResult(
                point=p,
                source_value=None if main is None else getattr(main, p.champ),
                error=None if main is None else point_error(p, main),
                neighbours=neighbours,
            )
        )
    return results


def windows(points: Sequence[ReferencePoint]) -> list[tuple[datetime, datetime]]:
    """Plages M1 à demander : une par journée de points, avec une marge autour."""
    by_day: dict[object, list[ReferencePoint]] = {}
    for p in points:
        by_day.setdefault(p.ts_open.date(), []).append(p)
    spans = []
    for day_points in by_day.values():
        start = min(p.ts_open for p in day_points) - MARGIN
        end = max(p.ts_open + p.ut * M1 for p in day_points) + MARGIN
        spans.append((start, end))
    return sorted(spans)


async def fetch_for(feed: PriceFeed, points: Sequence[ReferencePoint]) -> list[Candle]:
    found: dict[datetime, Candle] = {}
    for start, end in windows(points):
        for c in await feed.history(start, end):
            found.setdefault(c.ts_open, c)
    return [found[ts] for ts in sorted(found)]


async def oldest_candle(
    feed: PriceFeed, now: datetime, horizon: timedelta = HORIZON
) -> datetime | None:
    """La plus ancienne bougie M1 fournie, en avançant semaine par semaine depuis
    `now − horizon` jusqu'à la première semaine qui contient des bougies."""
    week = timedelta(days=7)
    end = now.astimezone(UTC).replace(second=0, microsecond=0)
    cursor = end - horizon
    while cursor < end:
        stop = min(cursor + week, end)
        candles = await feed.history(cursor, stop)
        if candles:
            return candles[0].ts_open
        cursor = stop
    return None


@dataclass(frozen=True)
class Summary:
    count: int
    missing: int
    share_ok: float
    mean_abs: Decimal | None
    max_abs: Decimal | None

    @property
    def close_enough(self) -> bool:
        return self.count > 0 and self.share_ok >= TARGET_SHARE


def summarize(results: Sequence[PointResult]) -> Summary:
    """Tous les points comptent. Un point sans bougie chez la source compte comme raté."""
    errors = [r.error for r in results if r.error is not None]
    return Summary(
        count=len(results),
        missing=len(results) - len(errors),
        share_ok=(sum(r.ok for r in results) / len(results)) if results else 0.0,
        mean_abs=(sum(errors, Decimal(0)) / len(errors)).quantize(Decimal("0.0001"))
        if errors
        else None,
        max_abs=max(errors) if errors else None,
    )


def pct(share: float) -> str:
    return f"{round(share * 100)} %"


def _pips(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    # USD/JPY : 1 pip = 0,01.
    return f"{value} ({(value * 100).normalize():f} pip)"


def _summary_line(label: str, s: Summary) -> str:
    return (
        f"| {label} | {s.count} | {pct(s.share_ok)} | {_pips(s.mean_abs)} | "
        f"{_pips(s.max_abs)} | {s.missing} |"
    )


def render_compare(
    source: str,
    price_kind: str,
    results: Sequence[PointResult],
    oldest: datetime | None,
    at: datetime,
) -> str:
    total = summarize(results)
    verdict = (
        f"**Oui** : {pct(total.share_ok)} des points à 0,3 pip ou moins (objectif 90 %)."
        if total.close_enough
        else f"**Non** : {pct(total.share_ok)} des points à 0,3 pip ou moins, sous "
        "l'objectif de 90 %. D'après la spec, la source est gardée quand même si son "
        "historique et son direct fonctionnent, et cet écart doit être reporté dans "
        "la section *Decision* de la spec 0002."
    )
    lines = [
        "## Écart avec OANDA",
        "",
        f"Mesure du {at:%Y-%m-%d à %H:%M} UTC. Source `{source}`, prix fourni : "
        f"**{price_kind}**.",
        "",
        f"Assez proche d'OANDA ? {verdict}",
        "",
        "| Points | Nombre | À 0,3 pip ou moins | Écart moyen absolu | Écart max | "
        "Sans bougie |",
        "|---|---|---|---|---|---|",
        _summary_line("Tous", total),
    ]
    for ut in sorted({r.point.ut for r in results}):
        lines.append(
            _summary_line(f"M{ut}", summarize([r for r in results if r.point.ut == ut]))
        )
    for kind in PointType:
        subset = [r for r in results if r.point.type is kind]
        if subset:
            lines.append(_summary_line(f"`{kind}`", summarize(subset)))
    shifted = [r for r in results if r.shift_hint is not None]
    lines += [
        "",
        "Les lignes M3 et M5 portent sur des bougies reconstruites depuis le M1 (AC-7).",
        "",
        "## Profondeur d'historique M1",
        "",
        (
            f"Plus ancienne bougie obtenue : **{oldest:%Y-%m-%d %H:%M} UTC** "
            f"(recherche sur 2 ans)."
            if oldest is not None
            else "Aucune bougie obtenue sur les 2 dernières années."
        ),
        "",
        "## Décalage d'une minute",
        "",
        (
            f"{len(shifted)} point(s) raté(s) collent à une bougie voisine : un décalage "
            "d'heure est possible, à regarder de près (tableau ci-dessous, colonne "
            "*Voisine*)."
            if shifted
            else "Aucun point raté ne colle mieux à la bougie d'avant ou d'après : pas "
            "de signe de décalage d'une minute."
        ),
        "",
        "## Détail des points",
        "",
        "| Capture | UT | Type | Bougie (UTC) | Champ | OANDA | Source | Écart | "
        "Voisine |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        p = r.point
        hint = {None: "", -1: "avant", 1: "après"}[r.shift_hint]
        mark = "" if r.ok else " ✗"
        lines.append(
            f"| {p.capture} | M{p.ut} | {p.type} | {p.ts_open:%Y-%m-%d %H:%M} | "
            f"{p.champ} | {p.prix} | {r.source_value or 'absente'} | "
            f"{r.error if r.error is not None else 'n/a'}{mark} | {hint} |"
        )
    return "\n".join(lines)


def render_unavailable(title: str, reason: str, at: datetime) -> str:
    return (
        f"## {title}\n\n{at:%Y-%m-%d %H:%M} UTC : source **indisponible** ({reason})."
    )


@dataclass(frozen=True)
class MinuteResult:
    ts_open: datetime
    # Secondes entre la fin de la minute et la réception de sa bougie ; None si manquée.
    delay: float | None
    error: str | None = None


def render_live(source: str, minutes: Sequence[MinuteResult], at: datetime) -> str:
    received = [m for m in minutes if m.delay is not None]
    delays = sorted(m.delay for m in received if m.delay is not None)
    missed = len(minutes) - len(received)
    status = (
        "**réussi** : chaque minute est arrivée"
        if minutes and not missed
        else f"**échoué** : {missed} minute(s) manquée(s) sur {len(minutes)}"
    )
    lines = [
        "## Test du direct",
        "",
        f"Test commencé le {at:%Y-%m-%d à %H:%M} UTC, source `{source}`, "
        f"{len(minutes)} minutes. Résultat : {status}.",
        "",
        f"- Minutes reçues : {len(received)}",
        f"- Minutes manquées (rien après 60 secondes) : {missed}",
    ]
    if delays:
        p95 = delays[max(0, round(0.95 * len(delays)) - 1)]
        lines += [
            f"- Délai après la fin de la minute : médiane "
            f"{statistics.median(delays):.1f} s, 95 % sous {p95:.1f} s, "
            f"maximum {delays[-1]:.1f} s",
            f"- Minutes reçues en moins de 10 secondes : "
            f"{sum(d < 10 for d in delays)} sur {len(minutes)}",
        ]
    lines += ["", "| Minute (UTC) | Délai | Erreur |", "|---|---|---|"]
    for m in minutes:
        delay = "manquée" if m.delay is None else f"{m.delay:.1f} s"
        lines.append(f"| {m.ts_open:%Y-%m-%d %H:%M} | {delay} | {m.error or ''} |")
    return "\n".join(lines)


REPORT_TITLE = "# Mesure de la source de prix contre OANDA (spec 0002)"
_SECTION = re.compile(r"<!-- (\w+):début -->.*?<!-- \1:fin -->", re.S)


def write_section(path: Path, name: str, body: str) -> None:
    """Remplace la section `name` du rapport (ou l'ajoute), sans toucher aux autres."""
    block = f"<!-- {name}:début -->\n{body}\n<!-- {name}:fin -->"
    text = path.read_text(encoding="utf-8") if path.exists() else REPORT_TITLE + "\n"
    sections = {m.group(1): m.group(0) for m in _SECTION.finditer(text)}
    sections[name] = block
    order = ["compare", "live"] + sorted(
        k for k in sections if k not in ("compare", "live")
    )
    out = [REPORT_TITLE, ""]
    out += [sections[k] + "\n" for k in order if k in sections]
    path.write_text("\n".join(out), encoding="utf-8")


def error_text(exc: FeedError) -> str:
    return f"{exc.cause} : {exc}"
