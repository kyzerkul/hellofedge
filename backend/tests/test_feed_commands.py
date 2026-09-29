"""Commandes `hellofedge feed compare` et `feed live-test` (spec 0002, AC-2),
de bout en bout : vraie base pour le jeton, faux serveur cTrader, vrai fichier de référence."""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fake_ctrader import FakeCTrader
from test_ctrader_feed import Market, minutes
from test_measure import FakeClock

from hellofedge import cli
from hellofedge.config import Settings
from hellofedge.data.ctrader.protocol import Msg
from hellofedge.data.feed import FeedUnavailable
from hellofedge.data.reference import load_reference

REFERENCE = Path(__file__).parents[2] / "exemples" / "reference_oanda.csv"
ACCOUNT = 4242
M1 = timedelta(minutes=1)


def settings(db_url: str) -> Settings:
    return Settings(
        database_url=db_url,
        ctrader_client_id="app-id",
        ctrader_client_secret="app-secret",
        ctrader_account_id=ACCOUNT,
        ctrader_access_token="acces-env",
        ctrader_refresh_token="renouv-env",
    )


def fill_matching(market: Market, points) -> None:
    """Des bougies M1 qui donnent exactement les prix OANDA des points `exact` M1."""
    for p in points:
        for i in range(-20, 20):
            ts = p.ts_open + i * M1
            market.bars.setdefault(
                ts, {"utcTimestampInMinutes": minutes(ts), "low": 15_000_000}
            )
    for p in points:
        if p.ut == 1 and p.champ == "open" and p.type == "exact":
            raw = int(p.prix * 100_000)
            market.bars[p.ts_open] = {
                "utcTimestampInMinutes": minutes(p.ts_open),
                "low": raw,
            }


@pytest.mark.asyncio
async def test_compare_writes_the_report_from_the_real_reference_file(
    db_url, clean_token, on_fake, tmp_path
):
    points = load_reference(REFERENCE)
    report = tmp_path / "mesure_sources.md"
    now = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
    async with FakeCTrader() as fake:
        market = Market(fake)
        fill_matching(market, points)
        on_fake(fake)

        summary = await cli.feed_compare(settings(db_url), now, REFERENCE, report)

    text_ = report.read_text(encoding="utf-8")
    assert summary is not None and summary.count == len(points)
    assert "## Écart avec OANDA" in text_ and "## Profondeur d'historique M1" in text_
    assert "prix fourni : **bid**" in text_
    # La plus ancienne bougie du faux serveur est celle du premier point, moins 20 minutes.
    oldest = min(p.ts_open for p in points) - 20 * M1
    assert f"{oldest:%Y-%m-%d %H:%M} UTC" in text_
    # Le compte a bien été authentifié avec le jeton en base, jamais renouvelé.
    assert fake.of_type(Msg.REFRESH_TOKEN_REQ) == []
    assert (
        fake.of_type(Msg.ACCOUNT_AUTH_REQ)[0]["payload"]["accessToken"] == "acces-env"
    )


@pytest.mark.asyncio
async def test_compare_notes_an_unreachable_source_in_the_report(
    db_url, clean_token, on_fake, tmp_path
):
    report = tmp_path / "mesure_sources.md"
    now = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
    async with FakeCTrader() as fake:
        on_fake(fake)
    # Le serveur est arrêté : la connexion échoue.

    with pytest.raises(FeedUnavailable):
        await cli.feed_compare(settings(db_url), now, REFERENCE, report)

    assert "source **indisponible**" in report.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_live_test_measures_each_minute(db_url, clean_token, on_fake, tmp_path):
    report = tmp_path / "mesure_sources.md"
    start = datetime(2026, 9, 29, 10, 0, 20, tzinfo=UTC)
    first = start.replace(second=0)
    clock = FakeClock(start)
    async with FakeCTrader() as fake:
        market = Market(fake)
        # Les minutes 10h00 et 10h02 existent, 10h01 ne viendra jamais.
        for ts in (first, first + 2 * M1):
            market.bars[ts] = {"utcTimestampInMinutes": minutes(ts), "low": 15_000_000}
        on_fake(fake, clock=clock)

        results = await cli.feed_live_test(
            settings(db_url), 3, report, clock=clock, sleep=clock.sleep
        )

    assert [r.delay for r in results] == [3.0, None, 3.0]
    text_ = report.read_text(encoding="utf-8")
    assert "## Test du direct" in text_
    assert "**échoué** : 1 minute(s) manquée(s) sur 3" in text_


# Commandes `feed ctrader-token --reseed` et `feed ctrader-accounts`, lancées par
# le vrai point d'entrée `hellofedge` (spec 0002, AC-13, *Commandes et surface*).

ENV_ACCESS = "acces-env-cli-111"
ENV_REFRESH = "renouv-env-cli-222"


@pytest.fixture
def cli_env(monkeypatch, db_url, clean_token):
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("CTRADER_CLIENT_ID", "app-id")
    monkeypatch.setenv("CTRADER_CLIENT_SECRET", "app-secret")
    monkeypatch.setenv("CTRADER_ACCESS_TOKEN", ENV_ACCESS)
    monkeypatch.setenv("CTRADER_REFRESH_TOKEN", ENV_REFRESH)
    return monkeypatch


async def stored_token(db_url):
    from hellofedge.data.ctrader import token as ctoken
    from hellofedge.db import make_engine

    engine = make_engine(db_url)
    try:
        return await ctoken.load(engine)
    finally:
        await engine.dispose()


def point_client_at(monkeypatch, fake: FakeCTrader) -> None:
    from hellofedge.data.ctrader.client import CTraderClient

    monkeypatch.setattr(
        cli,
        "make_client",
        lambda settings: CTraderClient(fake.url, "app-id", "app-secret"),
    )


class TestCtraderToken:
    def test_reseed_stores_the_environment_token(self, cli_env, db_url, capsys):
        code = cli.main(["feed", "ctrader-token", "--reseed"])

        out = capsys.readouterr()
        assert code == 0
        assert "Jeton remplacé" in out.out
        token = asyncio.run(stored_token(db_url))
        assert token is not None and token.access_token == ENV_ACCESS
        assert token.refresh_token == ENV_REFRESH

    def test_reseed_never_prints_the_token(self, cli_env, capsys):
        cli.main(["feed", "ctrader-token", "--reseed"])

        out = capsys.readouterr()
        for secret in (ENV_ACCESS, ENV_REFRESH):
            assert secret not in out.out and secret not in out.err

    def test_reseed_without_environment_token_stops_clearly(self, cli_env, capsys):
        cli_env.delenv("CTRADER_ACCESS_TOKEN")

        code = cli.main(["feed", "ctrader-token", "--reseed"])

        assert code == 1
        assert capsys.readouterr().err.startswith("Arrêt : CTRADER_ACCESS_TOKEN")

    def test_the_reseed_flag_is_required(self, cli_env):
        with pytest.raises(SystemExit) as exc:
            cli.main(["feed", "ctrader-token"])

        assert exc.value.code == 2


class TestCtraderAccounts:
    ACCOUNTS = {
        "accessToken": ENV_ACCESS,
        "ctidTraderAccount": [
            {
                "ctidTraderAccountId": 4242,
                "isLive": False,
                "traderLogin": 555,
                "brokerTitleShort": "IC Markets",
            },
            {"ctidTraderAccountId": 9999, "isLive": True},
        ],
    }

    def run(self, fake_reply, monkeypatch):
        async def serve():
            async with FakeCTrader() as fake:
                fake.on(Msg.GET_ACCOUNTS_BY_ACCESS_TOKEN_REQ, fake_reply)
                point_client_at(monkeypatch, fake)
                code = await asyncio.to_thread(cli.main, ["feed", "ctrader-accounts"])
                return code, fake.of_type(Msg.GET_ACCOUNTS_BY_ACCESS_TOKEN_REQ)

        return asyncio.run(serve())

    def test_lists_each_account_with_demo_or_live_and_broker(self, cli_env, capsys):
        code, asked = self.run(
            lambda p: (Msg.GET_ACCOUNTS_BY_ACCESS_TOKEN_RES, self.ACCOUNTS), cli_env
        )

        out = capsys.readouterr().out
        assert code == 0
        assert "4242  démo   courtier IC Markets  login 555" in out
        assert "9999  réel   courtier ?  login ?" in out
        assert "CTRADER_ACCOUNT_ID" in out
        assert [a["payload"] for a in asked] == [{"accessToken": ENV_ACCESS}]

    def test_says_so_when_no_account_is_linked(self, cli_env, capsys):
        code, _ = self.run(
            lambda p: (Msg.GET_ACCOUNTS_BY_ACCESS_TOKEN_RES, {"accessToken": "x"}),
            cli_env,
        )

        assert code == 0
        assert "Aucun compte cTrader lié à ce jeton." in capsys.readouterr().out

    def test_a_refused_token_stops_clearly_without_printing_it(self, cli_env, capsys):
        from fake_ctrader import error

        code, _ = self.run(lambda p: error("CH_ACCESS_TOKEN_INVALID"), cli_env)

        out = capsys.readouterr()
        assert code == 1
        assert "Arrêt : cTrader refuse" in out.err
        assert ENV_ACCESS not in out.out + out.err

    def test_missing_app_credentials_stop_clearly(self, cli_env, capsys):
        cli_env.delenv("CTRADER_CLIENT_ID")

        code = cli.main(["feed", "ctrader-accounts"])

        assert code == 1
        assert "CTRADER_CLIENT_ID" in capsys.readouterr().err
