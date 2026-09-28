"""Commande `hellofedge` : les opérations ponctuelles (spec 0002).

- `hellofedge feed ctrader-accounts` : liste les comptes cTrader liés au jeton, pour
  trouver le `ctidTraderAccountId` à mettre dans `CTRADER_ACCOUNT_ID`.
- `hellofedge feed ctrader-token --reseed` : remplace le jeton en base par celui de
  l'environnement, après une régénération manuelle.

Ces commandes ne renouvellent jamais le jeton : c'est le rôle du seul `worker`.
Elles n'affichent jamais un jeton.
"""

import argparse
import asyncio
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from hellofedge.config import Settings, get_settings
from hellofedge.data.ctrader import token as ctoken
from hellofedge.data.ctrader.protocol import Msg
from hellofedge.data.feed import FeedError
from hellofedge.data.sources import ConfigMissing, make_client
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
    except (ConfigMissing, ctoken.TokenMissing, ctoken.TokenExpiringSoon) as exc:
        print(f"Arrêt : {exc}", file=sys.stderr)
        return 1
    except FeedError as exc:
        print(f"Arrêt : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
