"""Jeton cTrader (spec 0002, AC-13) : base réelle et faux serveur local."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fake_ctrader import FakeCTrader, error
from sqlalchemy import text
from test_migrations import alembic

from hellofedge.config import Settings
from hellofedge.data.ctrader import token as ctoken
from hellofedge.data.ctrader.client import CTraderClient
from hellofedge.data.ctrader.protocol import Msg
from hellofedge.data.feed import FeedAuthError
from hellofedge.db import make_engine
from hellofedge.worker import WORKER_LOCK_KEY

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
ENV_ACCESS = "acces-env-123"
ENV_REFRESH = "renouv-env-456"
NEW_ACCESS = "acces-neuf-789"
NEW_REFRESH = "renouv-neuf-000"


def settings(db_url: str) -> Settings:
    return Settings(
        database_url=db_url,
        ctrader_client_id="app-id",
        ctrader_client_secret="app-secret",
        ctrader_access_token=ENV_ACCESS,
        ctrader_refresh_token=ENV_REFRESH,
    )


@pytest_asyncio.fixture
async def engine(db_url):
    # La table vient de la vraie migration, comme en production.
    result = alembic("upgrade", "head", database_url=db_url)
    assert result.returncode == 0, result.stderr
    eng = make_engine(db_url)
    async with eng.begin() as conn:
        await conn.execute(text("DELETE FROM provider_token"))
    yield eng
    await eng.dispose()


def refresh_reply(payload):
    return (
        Msg.REFRESH_TOKEN_RES,
        {
            "accessToken": NEW_ACCESS,
            "refreshToken": NEW_REFRESH,
            "tokenType": "bearer",
            "expiresIn": 2_628_000,
        },
    )


def test_token_lock_is_not_the_worker_lock():
    assert ctoken.TOKEN_LOCK_KEY != WORKER_LOCK_KEY


def test_seed_lifetime_sits_between_the_two_thresholds():
    # Le worker renouvelle au premier passage, les commandes marchent tout de suite.
    assert ctoken.COMMAND_MIN_VALIDITY < ctoken.SEED_LIFETIME < ctoken.RENEW_BEFORE


def test_token_repr_hides_the_secret():
    tok = ctoken.Token(ENV_ACCESS, ENV_REFRESH, NOW)
    assert ENV_ACCESS not in repr(tok) and ENV_REFRESH not in repr(tok)


@pytest.mark.asyncio
async def test_first_token_comes_from_the_environment(engine, db_url):
    tok = await ctoken.ensure_seeded(engine, settings(db_url), NOW)

    assert tok.access_token == ENV_ACCESS
    assert tok.expires_at == NOW + ctoken.SEED_LIFETIME


@pytest.mark.asyncio
async def test_seed_never_overwrites_a_stored_token(engine, db_url):
    await ctoken.ensure_seeded(engine, settings(db_url), NOW)
    later = NOW + timedelta(days=2)

    tok = await ctoken.ensure_seeded(engine, settings(db_url), later)

    assert tok.expires_at == NOW + ctoken.SEED_LIFETIME


@pytest.mark.asyncio
async def test_missing_environment_token_is_a_clear_error(engine, db_url):
    s = Settings(database_url=db_url)
    with pytest.raises(ctoken.TokenMissing):
        await ctoken.ensure_seeded(engine, s, NOW)


@pytest.mark.asyncio
async def test_commands_use_the_seeded_token_right_away(engine, db_url):
    tok = await ctoken.token_for_command(engine, settings(db_url), NOW)
    assert tok.access_token == ENV_ACCESS


@pytest.mark.asyncio
async def test_commands_refuse_a_token_about_to_expire(engine, db_url):
    await ctoken.ensure_seeded(engine, settings(db_url), NOW)
    almost = NOW + ctoken.SEED_LIFETIME - timedelta(hours=12)

    with pytest.raises(ctoken.TokenExpiringSoon):
        await ctoken.token_for_command(engine, settings(db_url), almost)


@pytest.mark.asyncio
async def test_reseed_replaces_the_stored_token(engine, db_url):
    await ctoken._write(engine, ctoken.Token("vieux", "vieux", NOW), NOW, replace=False)

    await ctoken.reseed(engine, settings(db_url), NOW)

    tok = await ctoken.load(engine)
    assert tok is not None and tok.access_token == ENV_ACCESS


@pytest.mark.asyncio
async def test_worker_renews_the_seeded_token_on_first_pass(engine, db_url):
    async with FakeCTrader() as fake:
        fake.on(Msg.REFRESH_TOKEN_REQ, refresh_reply)
        client = CTraderClient(fake.url, "app-id", "app-secret")
        await client.connect()
        try:
            tok = await ctoken.refresh_if_needed(engine, client, settings(db_url), NOW)
        finally:
            await client.close()

        sent = fake.of_type(Msg.REFRESH_TOKEN_REQ)
    assert [s["payload"] for s in sent] == [{"refreshToken": ENV_REFRESH}]
    assert tok.access_token == NEW_ACCESS
    stored = await ctoken.load(engine)
    assert stored is not None
    assert stored.access_token == NEW_ACCESS
    assert stored.refresh_token == NEW_REFRESH
    assert stored.expires_at == NOW + timedelta(seconds=2_628_000)


@pytest.mark.asyncio
async def test_two_simultaneous_passes_renew_only_once(engine, db_url):
    async with FakeCTrader() as fake:
        fake.on(Msg.REFRESH_TOKEN_REQ, refresh_reply)
        client = CTraderClient(fake.url, "app-id", "app-secret")
        await client.connect()
        try:
            s = settings(db_url)
            await asyncio.gather(
                ctoken.refresh_if_needed(engine, client, s, NOW),
                ctoken.refresh_if_needed(engine, client, s, NOW),
            )
        finally:
            await client.close()

        assert len(fake.of_type(Msg.REFRESH_TOKEN_REQ)) == 1


@pytest.mark.asyncio
async def test_no_renewal_while_seven_days_remain(engine, db_url):
    fresh = ctoken.Token("a", "r", NOW + timedelta(days=20))
    await ctoken._write(engine, fresh, NOW, replace=False)
    async with FakeCTrader() as fake:
        client = CTraderClient(fake.url, "app-id", "app-secret")
        await client.connect()
        try:
            await ctoken.refresh_if_needed(engine, client, settings(db_url), NOW)
        finally:
            await client.close()

        assert fake.of_type(Msg.REFRESH_TOKEN_REQ) == []


@pytest.mark.asyncio
async def test_a_lost_renewed_token_opens_an_auth_outage(
    engine, db_url, monkeypatch, caplog
):
    caplog.set_level(logging.DEBUG, logger="hellofedge")
    await ctoken.ensure_seeded(engine, settings(db_url), NOW)
    real_write = ctoken._write
    writes = []

    async def failing_write(eng, tok, now, *, replace):
        if tok.access_token == NEW_ACCESS:
            writes.append(tok)
            raise OSError("base indisponible")
        await real_write(eng, tok, now, replace=replace)

    monkeypatch.setattr(ctoken, "_write", failing_write)
    naps = []

    async def no_sleep(seconds):
        naps.append(seconds)

    async with FakeCTrader() as fake:
        fake.on(Msg.REFRESH_TOKEN_REQ, refresh_reply)
        client = CTraderClient(fake.url, "app-id", "app-secret")
        await client.connect()
        try:
            with pytest.raises(FeedAuthError) as info:
                await ctoken.refresh_if_needed(
                    engine, client, settings(db_url), NOW, sleep=no_sleep
                )
        finally:
            await client.close()

    assert info.value.cause == "auth"
    assert "--reseed" in str(info.value)
    assert len(writes) == ctoken.SAVE_ATTEMPTS
    assert len(naps) == ctoken.SAVE_ATTEMPTS - 1
    for secret in (NEW_ACCESS, NEW_REFRESH, ENV_ACCESS, ENV_REFRESH):
        assert secret not in caplog.text
        assert secret not in str(info.value)


@pytest.mark.asyncio
async def test_account_refusal_rereads_the_token_and_retries_once(engine, db_url):
    await ctoken.ensure_seeded(engine, settings(db_url), NOW)
    answers = iter([error("CH_ACCESS_TOKEN_INVALID"), (Msg.ACCOUNT_AUTH_RES, {})])
    async with FakeCTrader() as fake:
        fake.on(Msg.ACCOUNT_AUTH_REQ, lambda p: next(answers))
        client = CTraderClient(fake.url, "app-id", "app-secret")
        await client.connect()
        try:
            await ctoken.authorize_account(engine, client, 42)
        finally:
            await client.close()

        tries = fake.of_type(Msg.ACCOUNT_AUTH_REQ)
    assert len(tries) == 2
    assert tries[0]["payload"] == {
        "ctidTraderAccountId": 42,
        "accessToken": ENV_ACCESS,
    }


@pytest.mark.asyncio
async def test_second_account_refusal_is_an_auth_error(engine, db_url):
    await ctoken.ensure_seeded(engine, settings(db_url), NOW)
    async with FakeCTrader() as fake:
        fake.on(Msg.ACCOUNT_AUTH_REQ, lambda p: error("CH_ACCESS_TOKEN_INVALID"))
        client = CTraderClient(fake.url, "app-id", "app-secret")
        await client.connect()
        try:
            with pytest.raises(FeedAuthError):
                await ctoken.authorize_account(engine, client, 42)
            assert client.authorized_account is None
        finally:
            await client.close()

        assert len(fake.of_type(Msg.ACCOUNT_AUTH_REQ)) == 2


@pytest.mark.asyncio
async def test_already_logged_in_is_not_a_failure(engine, db_url):
    await ctoken.ensure_seeded(engine, settings(db_url), NOW)
    async with FakeCTrader() as fake:
        fake.on(Msg.ACCOUNT_AUTH_REQ, lambda p: error("ALREADY_LOGGED_IN"))
        client = CTraderClient(fake.url, "app-id", "app-secret")
        await client.connect()
        try:
            await ctoken.authorize_account(engine, client, 42)
            assert client.authorized_account == 42
        finally:
            await client.close()
