"""Commande `hellofedge` : les opérations ponctuelles (spec 0002).

- `hellofedge feed ctrader-accounts` : liste les comptes cTrader liés au jeton, pour
  trouver le `ctidTraderAccountId` à mettre dans `CTRADER_ACCOUNT_ID`.
- `hellofedge feed ctrader-token --reseed` : remplace le jeton en base par celui de
  l'environnement, après une régénération manuelle.
- `hellofedge feed compare` : mesure l'écart de la source avec les points OANDA et
  sa profondeur d'historique, puis écrit `exemples/mesure_sources.md`.
- `hellofedge feed live-test` : lit le direct pendant N minutes et ajoute le délai
  de chaque minute au même rapport.
- `hellofedge feed backfill` : charge en base l'historique M1 de la source active
  (2 ans par défaut, ce que le courtier fournit). Relancer ne crée aucun doublon.

Sur le VPS, le dossier `exemples/` n'est pas dans l'image : on le monte, par exemple
`docker compose run --rm -v "$PWD/../exemples:/app/exemples" api hellofedge feed compare`.

Ces commandes ne renouvellent jamais le jeton : c'est le rôle du seul `worker`.
Elles n'affichent jamais un jeton.
"""

import argparse
import asyncio
import logging
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from hellofedge.config import Settings, get_settings
from hellofedge.data.ctrader import token as ctoken
from hellofedge.data import measure
from hellofedge.data.backfill import BackfillResult, backfill
from hellofedge.data.candle import M1
from hellofedge.data.ctrader.protocol import Msg
from hellofedge.data.feed import FeedError
from hellofedge.data.live import Clock, Sleep, floor_minute, wait_for_minute
from hellofedge.data.reference import ReferenceFileError, load_reference
from hellofedge.data.sources import ConfigMissing, make_client, open_feed
from hellofedge.db import make_engine
from hellofedge.logs import setup_logging

log = logging.getLogger("hellofedge.cli")


def format_accounts(payload: dict[str, Any]) -> list[str]:
    lines = []
    for acc in payload.get("ctidTraderAccount") or []:
        kind = "réel" if acc.get("isLive") else "démo"
        broker = acc.get("brokerTitleShort") or "?"
        lines.append(
            f"{acc.get('ctidTraderAccountId')}  {kind:5}  courtier {broker}  "
            f"login {acc.get('traderLogin', '?')}"
        )
    return lines


async def ctrader_accounts(settings: Settings, now: datetime) -> list[str]:
    engine = make_engine(settings.database_url)
    client = make_client(settings)
    try:
        tok = await ctoken.token_for_command(engine, settings, now)
        await client.connect()
        payload = await client.request(
            Msg.GET_ACCOUNTS_BY_ACCESS_TOKEN_REQ, {"accessToken": tok.access_token}
        )
        return format_accounts(payload)
    finally:
        await client.close()
        await engine.dispose()


async def ctrader_reseed(settings: Settings, now: datetime) -> ctoken.Token:
    engine = make_engine(settings.database_url)
    try:
        return await ctoken.reseed(engine, settings, now)
    finally:
        await engine.dispose()


DEFAULT_REFERENCE = Path("../exemples/reference_oanda.csv")
DEFAULT_REPORT = Path("../exemples/mesure_sources.md")


async def feed_compare(
    settings: Settings, now: datetime, reference: Path, report: Path
) -> measure.Summary | None:
    """Mesure la source active. Source injoignable : « indisponible » dans le rapport."""
    points = load_reference(reference)
    engine = make_engine(settings.database_url)
    try:
        await ctoken.token_for_command(engine, settings, now)
        feed = open_feed(settings, engine)
        try:
            m1 = await measure.fetch_for(feed, points)
            results = measure.score(points, m1)
            oldest = await measure.oldest_candle(feed, now)
        except FeedError as exc:
            measure.write_section(
                report,
                "compare",
                measure.render_unavailable(
                    "Écart avec OANDA", measure.error_text(exc), now
                ),
            )
            raise
        finally:
            await feed.aclose()
        measure.write_section(
            report,
            "compare",
            measure.render_compare(feed.name, feed.price_kind, results, oldest, now),
        )
        return measure.summarize(results)
    finally:
        await engine.dispose()


async def feed_live_test(
    settings: Settings,
    minutes: int,
    report: Path,
    *,
    clock: Clock = lambda: datetime.now(UTC),
    sleep: Sleep = asyncio.sleep,
) -> list[measure.MinuteResult]:
    """Lit le direct pendant `minutes` minutes, à partir de la minute en cours."""
    started = clock()
    engine = make_engine(settings.database_url)
    try:
        await ctoken.token_for_command(engine, settings, started)
        feed = open_feed(settings, engine)
        results = []
        try:
            first = floor_minute(started)
            for i in range(minutes):
                attempt = await wait_for_minute(
                    feed, first + i * M1, clock=clock, sleep=sleep
                )
                error = None
                if attempt.candle is None and attempt.last_error is not None:
                    error = measure.error_text(attempt.last_error)
                results.append(
                    measure.MinuteResult(attempt.ts_open, attempt.delay, error)
                )
        finally:
            await feed.aclose()
        measure.write_section(
            report, "live", measure.render_live(feed.name, results, started)
        )
        return results
    finally:
        await engine.dispose()


HISTORY_DEPTH = timedelta(days=730)


def utc_minute(value: str) -> datetime:
    """Une date (`2024-10-01`) ou une heure ISO, lue en UTC, ramenée à la minute."""
    ts = datetime.fromisoformat(value)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(second=0, microsecond=0)


async def feed_backfill(
    settings: Settings, now: datetime, start: datetime | None, end: datetime | None
) -> BackfillResult:
    end = end or now.replace(second=0, microsecond=0)
    start = start or end - HISTORY_DEPTH
    engine = make_engine(settings.database_url)
    try:
        await ctoken.token_for_command(engine, settings, now)
        feed = open_feed(settings, engine)
        try:
            return await backfill(engine, feed, start, end)
        finally:
            await feed.aclose()
    finally:
        await engine.dispose()


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hellofedge")
    groups = p.add_subparsers(dest="group", required=True)
    feed = groups.add_parser("feed", help="source de prix")
    cmds = feed.add_subparsers(dest="cmd", required=True)
    cmds.add_parser("ctrader-accounts", help="liste les comptes cTrader liés au jeton")
    tok = cmds.add_parser("ctrader-token", help="gestion du jeton cTrader")
    tok.add_argument(
        "--reseed",
        action="store_true",
        required=True,
        help="remplace le jeton en base par celui de l'environnement",
    )
    cmp = cmds.add_parser("compare", help="mesure l'écart de la source avec OANDA")
    cmp.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    cmp.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    live = cmds.add_parser("live-test", help="teste le direct pendant N minutes")
    live.add_argument("--minutes", type=int, default=30)
    live.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    bf = cmds.add_parser("backfill", help="charge l'historique M1 en base")
    bf.add_argument("--from", dest="start", type=utc_minute, help="défaut : 2 ans")
    bf.add_argument("--to", dest="end", type=utc_minute, help="défaut : maintenant")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    settings = get_settings()
    setup_logging(settings.log_level)
    now = datetime.now(UTC)
    try:
        if args.cmd == "ctrader-accounts":
            lines = asyncio.run(ctrader_accounts(settings, now))
            if not lines:
                print("Aucun compte cTrader lié à ce jeton.")
            else:
                print("\n".join(lines))
                print(
                    "Mets le numéro du compte démo IC Markets dans CTRADER_ACCOUNT_ID."
                )
        elif args.cmd == "ctrader-token":
            tok = asyncio.run(ctrader_reseed(settings, now))
            print(
                "Jeton remplacé. Le worker le renouvellera à son prochain passage "
                f"(expiration supposée : {tok.expires_at:%Y-%m-%d %H:%M} UTC)."
            )
        elif args.cmd == "compare":
            summary = asyncio.run(
                feed_compare(settings, now, args.reference, args.report)
            )
            assert summary is not None
            print(
                f"{measure.pct(summary.share_ok)} des {summary.count} points à 0,3 pip ou moins. "
                f"Rapport écrit dans {args.report}."
            )
        elif args.cmd == "live-test":
            results = asyncio.run(feed_live_test(settings, args.minutes, args.report))
            missed = sum(r.delay is None for r in results)
            print(
                f"{len(results) - missed} minutes reçues, {missed} manquées. "
                f"Rapport écrit dans {args.report}."
            )
            if missed:
                return 1
        elif args.cmd == "backfill":
            res = asyncio.run(feed_backfill(settings, now, args.start, args.end))
            oldest = (
                "aucune bougie"
                if res.oldest is None
                else f"{res.oldest:%Y-%m-%d %H:%M} UTC"
            )
            print(
                f"{res.inserted} bougies insérées, {res.ignored} déjà en base, "
                f"{res.revisions} révisions notées. Plus ancienne bougie obtenue : "
                f"{oldest}."
            )
    except (
        ConfigMissing,
        ctoken.TokenMissing,
        ctoken.TokenExpiringSoon,
        ReferenceFileError,
    ) as exc:
        print(f"Arrêt : {exc}", file=sys.stderr)
        return 1
    except FeedError as exc:
        print(f"Arrêt : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
