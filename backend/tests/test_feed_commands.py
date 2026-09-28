"""Commandes `hellofedge feed compare` et `feed live-test` (spec 0002, AC-2),
de bout en bout : vraie base pour le jeton, faux serveur cTrader, vrai fichier de référence."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from fake_ctrader import FakeCTrader
from sqlalchemy import text
from test_ctrader_feed import Market, minutes
from test_measure import FakeClock
from test_migrations import alembic

from hellofedge import cli
from hellofedge.config import Settings
from hellofedge.data.ctrader import token as ctoken
from hellofedge.data.ctrader.client import CTraderClient
from hellofedge.data.ctrader.feed import CTraderFeed
from hellofedge.data.ctrader.protocol import Msg
from hellofedge.data.feed import FeedUnavailable
from hellofedge.data.reference import load_reference
from hellofedge.db import make_engine

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


@pytest_asyncio.fixture
async def clean_token(db_url):
    result = alembic("upgrade", "head", database_url=db_url)
    assert result.returncode == 0, result.stderr
    eng = make_engine(db_url)
    async with eng.begin() as conn:
        await conn.execute(text("DELETE FROM provider_token"))
    await eng.dispose()


@pytest.fixture
def on_fake(monkeypatch):
    """Fait pointer `open_feed` des commandes vers le faux serveur."""

    def install(fake: FakeCTrader, clock=None):
        url = fake.url

        def open_feed(settings, engine):
            async def authorize(client, account_id):
                await ctoken.authorize_account(engine, client, account_id)

            kwargs = {} if clock is None else {"clock": clock}
            return CTraderFeed(
                CTraderClient(url, "app-id", "app-secret", bars_per_second=1000),
                settings.ctrader_account_id,
                settings.ctrader_symbol,
                authorize,
                **kwargs,
            )

        monkeypatch.setattr(cli, "open_feed", open_feed)

    return install


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
