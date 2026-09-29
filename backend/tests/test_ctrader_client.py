"""Client cTrader (spec 0002, AC-9 et AC-14), testé contre un faux serveur local."""

import asyncio
import logging
import time

import pytest
from fake_ctrader import FakeCTrader, error

from hellofedge.data.ctrader.client import CTraderClient, MessageNotAllowed, RateLimiter
from hellofedge.data.ctrader.protocol import SENDABLE, Msg, host_for
from hellofedge.data.feed import FeedAuthError, FeedRateLimited, FeedUnavailable

SECRET = "secret-de-test-123"

# Messages de trading de l'Open API (ordres, positions, compte en écriture).
TRADING_MESSAGES = {
    2106,  # NEW_ORDER_REQ
    2107,  # CANCEL_ORDER_REQ
    2108,  # AMEND_ORDER_REQ
    2109,  # AMEND_POSITION_SLTP_REQ
    2111,  # CLOSE_POSITION_REQ
}


def client_for(fake: FakeCTrader, **kwargs) -> CTraderClient:
    return CTraderClient(fake.url, "app-id", SECRET, **kwargs)


@pytest.mark.asyncio
async def test_connect_authenticates_the_application():
    async with FakeCTrader() as fake:
        client = client_for(fake)
        await client.connect()
        try:
            auth = fake.of_type(Msg.APPLICATION_AUTH_REQ)
            assert [a["payload"] for a in auth] == [
                {"clientId": "app-id", "clientSecret": SECRET}
            ]
            assert client.connected
        finally:
            await client.close()


def test_whitelist_holds_no_trading_message():
    assert SENDABLE.isdisjoint(TRADING_MESSAGES)


@pytest.mark.asyncio
async def test_a_message_outside_the_whitelist_is_never_sent():
    async with FakeCTrader() as fake:
        client = client_for(fake)
        await client.connect()
        try:
            with pytest.raises(MessageNotAllowed):
                await client.request(2106, {"symbolId": 4, "volume": 1000})
            await asyncio.sleep(0.05)
            assert fake.of_type(2106) == []
        finally:
            await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("code", "expected", "cause"),
    [
        ("CH_ACCESS_TOKEN_INVALID", FeedAuthError, "auth"),
        ("REQUEST_FREQUENCY_EXCEEDED", FeedRateLimited, "limite_api"),
        ("INVALID_REQUEST", FeedUnavailable, "erreur_api"),
    ],
)
async def test_provider_errors_map_to_feed_errors(code, expected, cause):
    async with FakeCTrader() as fake:
        fake.on(Msg.SYMBOLS_LIST_REQ, lambda p: error(code))
        client = client_for(fake)
        await client.connect()
        try:
            with pytest.raises(expected) as info:
                await client.request(Msg.SYMBOLS_LIST_REQ, {"ctidTraderAccountId": 1})
            assert info.value.cause == cause
            assert info.value.error_code == code
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_heartbeat_is_sent_regularly():
    async with FakeCTrader() as fake:
        client = client_for(fake, heartbeat_seconds=0.05)
        await client.connect()
        try:
            await asyncio.sleep(0.2)
            assert len(fake.of_type(Msg.HEARTBEAT_EVENT)) >= 2
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_no_answer_is_a_timeout():
    async with FakeCTrader() as fake:
        fake.on(Msg.VERSION_REQ, lambda p: None)
        client = client_for(fake, request_timeout=0.2)
        await client.connect()
        try:
            with pytest.raises(FeedUnavailable) as info:
                await client.request(Msg.VERSION_REQ, {})
            assert info.value.cause == "timeout"
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_a_dropped_connection_fails_the_pending_request():
    async with FakeCTrader() as fake:
        fake.on(Msg.VERSION_REQ, lambda p: None)
        client = client_for(fake, request_timeout=5)
        await client.connect()
        try:
            pending = asyncio.create_task(client.request(Msg.VERSION_REQ, {}))
            await asyncio.sleep(0.05)
            await fake.drop_all()
            with pytest.raises(FeedUnavailable) as info:
                await pending
            assert info.value.cause == "reseau"
            await asyncio.sleep(0.05)
            assert not client.connected
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_unreachable_server_is_a_network_error():
    async with FakeCTrader() as fake:
        url = fake.url
    client = CTraderClient(url, "app-id", SECRET, request_timeout=1)
    with pytest.raises(FeedUnavailable) as info:
        await client.connect()
    assert info.value.cause == "reseau"


@pytest.mark.asyncio
async def test_rate_limiter_spaces_requests():
    limiter = RateLimiter(per_second=20)
    start = time.monotonic()
    await asyncio.gather(*(limiter.wait() for _ in range(5)))

    # 5 passages à 20 par seconde : au moins 4 intervalles de 50 ms.
    assert time.monotonic() - start >= 0.19


@pytest.mark.asyncio
async def test_secrets_never_reach_the_logs(caplog):
    caplog.set_level(logging.DEBUG, logger="hellofedge")
    async with FakeCTrader() as fake:
        client = client_for(fake)
        await client.connect()
        try:
            await client.request(Msg.REFRESH_TOKEN_REQ, {"refreshToken": SECRET})
        finally:
            await client.close()

    assert caplog.records
    assert SECRET not in caplog.text


def test_host_for_env():
    assert host_for("demo") == "wss://demo.ctraderapi.com:5036"
    with pytest.raises(ValueError):
        host_for("prod")


@pytest.mark.asyncio
async def test_a_silent_server_fails_fast_on_connect():
    # Un serveur qui accepte la connexion TCP mais ne répond jamais : le délai de
    # connexion, court, joue, pas celui des requêtes.
    async def mute(reader, writer):
        await asyncio.sleep(10)

    server = await asyncio.start_server(mute, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    client = CTraderClient(
        f"ws://127.0.0.1:{port}",
        "app-id",
        SECRET,
        connect_timeout=0.2,
        request_timeout=5,
    )
    start = time.monotonic()
    try:
        with pytest.raises(FeedUnavailable) as info:
            await client.connect()
    finally:
        server.close()
    assert info.value.cause == "timeout"
    assert time.monotonic() - start < 2


def test_connect_timeout_is_shorter_than_request_timeout():
    client = CTraderClient("ws://127.0.0.1:1", "app-id", SECRET)
    assert client._connect_timeout < client._request_timeout


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", [Msg.SYMBOLS_LIST_RES, Msg.OA_ERROR_RES])
async def test_a_payload_that_is_not_an_object_is_an_api_error(kind):
    # Même cause que le bug trouvé par /test : vaut pour toute réponse, erreurs
    # comprises (sinon `payload.get("errorCode")` échappait aussi).
    async with FakeCTrader() as fake:
        fake.on(Msg.SYMBOLS_LIST_REQ, lambda p: (kind, ["pas", "un", "objet"]))
        client = client_for(fake)
        await client.connect()
        try:
            with pytest.raises(FeedUnavailable) as info:
                await client.request(Msg.SYMBOLS_LIST_REQ, {"ctidTraderAccountId": 1})
        finally:
            await client.close()

    assert info.value.cause == "erreur_api"
