"""Commande `hellofedge` : les opérations ponctuelles (spec 0002).

- `hellofedge feed ctrader-accounts` : liste les comptes cTrader liés au jeton, pour
  trouver le `ctidTraderAccountId` à mettre dans `CTRADER_ACCOUNT_ID`.
- `hellofedge feed ctrader-token --reseed` : remplace le jeton en base par celui de
  l'environnement, après une régénération manuelle.
- `hellofedge feed compare` : mesure l'écart de la source avec les points OANDA et
  sa profondeur d'historique, puis écrit `exemples/mesure_sources.md`.
- `hellofedge feed live-test` : lit le direct pendant N minutes et ajoute le délai
  de chaque minute au même rapport.

Sur le VPS, le dossier `exemples/` n'est pas dans l'image : on le monte, par exemple
`docker compose run --rm -v "$PWD/../exemples:/app/exemples" api hellofedge feed compare`.

Ces commandes ne renouvellent jamais le jeton : c'est le rôle du seul `worker`.
Elles n'affichent jamais un jeton.
"""

import argparse
import asyncio
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hellofedge.config import Settings, get_settings
from hellofedge.data.ctrader import token as ctoken
from hellofedge.data import measure
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
