"""Adaptateur `ctrader_icmarkets` (spec 0002, AC-3, AC-4, AC-12), contre un faux serveur local."""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fake_ctrader import FakeCTrader, error

from hellofedge.config import Settings
from hellofedge.data.ctrader.client import CTraderClient
from hellofedge.data.ctrader.feed import CTraderFeed, decode_bar
from hellofedge.data.ctrader.protocol import Msg
from hellofedge.data.feed import FeedAuthError, FeedUnavailable
from hellofedge.data.sources import ConfigMissing, open_feed

ACCOUNT = 4242
USDJPY_ID = 4
M1 = timedelta(minutes=1)


def minutes(ts: datetime) -> int:
    return int(ts.timestamp()) // 60


def bar(ts: datetime, low: int = 15_917_400, **deltas: int) -> dict:
    return {"utcTimestampInMinutes": minutes(ts), "low": low, "volume": 12, **deltas}


class Market:
    """Le faux cTrader d'un compte démo : un symbole USDJPY à 3 décimales et des bougies."""

    def __init__(self, fake: FakeCTrader, *, digits: int = 3) -> None:
        self.bars: dict[datetime, dict] = {}
        self.digits = digits
        self.bar_requests: list[dict] = []
        # Au plus ce nombre de bougies par réponse, comme la troncature de cTrader.
        self.cap: int | None = None
        fake.on(
            Msg.SYMBOLS_LIST_REQ,
            lambda p: (
                Msg.SYMBOLS_LIST_RES,
                {
                    "symbol": [
                        {"symbolId": 1, "symbolName": "EURUSD"},
                        {"symbolId": USDJPY_ID, "symbolName": "USDJPY"},
                    ]
                },
            ),
        )
        fake.on(
            Msg.SYMBOL_BY_ID_REQ,
            lambda p: (
                Msg.SYMBOL_BY_ID_RES,
                {"symbol": [{"symbolId": USDJPY_ID, "digits": self.digits}]},
            ),
        )
        fake.on(Msg.GET_TRENDBARS_REQ, self._trendbars)

    def _trendbars(self, payload: dict):
        self.bar_requests.append(payload)
        start = datetime.fromtimestamp(payload["fromTimestamp"] / 1000, UTC)
        end = datetime.fromtimestamp(payload["toTimestamp"] / 1000, UTC)
        # Comme cTrader, la fin est incluse : c'est à l'adaptateur de l'exclure.
        found = [b for ts, b in sorted(self.bars.items()) if start <= ts <= end]
        if self.cap is not None and len(found) > self.cap:
            found = found[-self.cap :]
        return (Msg.GET_TRENDBARS_RES, {"trendbar": found, "period": 1})

    def fill(self, start: datetime, count: int) -> None:
        for i in range(count):
            ts = start + i * M1
            self.bars[ts] = bar(ts, deltaHigh=30, deltaClose=10, deltaOpen=5)


async def authorize(client: CTraderClient, account_id: int) -> None:
    await client.request(
        Msg.ACCOUNT_AUTH_REQ,
        {"ctidTraderAccountId": account_id, "accessToken": "jeton-test"},
    )
    client.authorized_account = account_id


def feed_for(fake: FakeCTrader, **kwargs) -> CTraderFeed:
    client = CTraderClient(fake.url, "app-id", "app-secret")
    return CTraderFeed(client, ACCOUNT, "USDJPY", authorize, **kwargs)


class TestDecode:
    def test_winter_bar_gets_its_prices_and_utc_open(self):
        # 15 janvier 2026, 10h47 UTC (heure d'hiver à Londres et New York).
        ts = datetime(2026, 1, 15, 10, 47, tzinfo=UTC)
        candle = decode_bar(
            bar(ts, low=15_917_400, deltaOpen=500, deltaHigh=2_300, deltaClose=1_100), 3
        )

        assert candle.ts_open == ts
        assert (candle.open, candle.high, candle.low, candle.close) == (
            Decimal("159.179"),
            Decimal("159.197"),
            Decimal("159.174"),
            Decimal("159.185"),
        )
        assert candle.tick_volume == 12

    def test_summer_bar_is_dated_at_the_opening_of_its_minute_in_utc(self):
        # 24 juillet 2026, 10h47 UTC : l'heure d'été ne décale rien.
        ts = datetime(2026, 7, 24, 10, 47, tzinfo=UTC)
        candle = decode_bar(bar(ts), 3)

        assert candle.ts_open == ts
        assert candle.ts_open.utcoffset() == timedelta(0)

    def test_missing_deltas_count_as_zero(self):
        ts = datetime(2026, 7, 24, 10, 47, tzinfo=UTC)
        candle = decode_bar(
            {"utcTimestampInMinutes": minutes(ts), "low": 15_917_400}, 3
        )

        assert candle.open == candle.high == candle.low == candle.close
        assert candle.tick_volume is None

    def test_prices_are_exact_decimals_with_3_places(self):
        ts = datetime(2026, 7, 24, 10, 47, tzinfo=UTC)
        candle = decode_bar(bar(ts, low=15_900_000, deltaHigh=200), 3)

        # 0,2 pip reste exactement 0.002.
        assert candle.high - candle.low == Decimal("0.002")
        assert candle.low.as_tuple().exponent == -3

    def test_json_numbers_sent_as_strings_are_accepted(self):
        ts = datetime(2026, 7, 24, 10, 47, tzinfo=UTC)
        candle = decode_bar(
            {
                "utcTimestampInMinutes": str(minutes(ts)),
                "low": "15917400",
                "deltaHigh": "100",
            },
            3,
        )

        assert candle.high == Decimal("159.175")


class TestHistory:
    @pytest.mark.asyncio
    async def test_reads_the_symbol_then_returns_sorted_bid_minutes(self):
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            market = Market(fake)
            market.fill(start, 5)
            feed = feed_for(fake)
            try:
                candles = await feed.history(start, start + 5 * M1)
            finally:
                await feed.aclose()

        assert [c.ts_open for c in candles] == [start + i * M1 for i in range(5)]
        assert market.bar_requests[0]["symbolId"] == USDJPY_ID
        assert market.bar_requests[0]["period"] == 1
        assert market.bar_requests[0]["ctidTraderAccountId"] == ACCOUNT
        assert len(fake.of_type(Msg.ACCOUNT_AUTH_REQ)) == 1

    @pytest.mark.asyncio
    async def test_end_is_excluded_even_when_the_server_includes_it(self):
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            Market(fake).fill(start, 5)
            feed = feed_for(fake)
            try:
                candles = await feed.history(start, start + 3 * M1)
            finally:
                await feed.aclose()

        assert [c.ts_open for c in candles] == [start, start + M1, start + 2 * M1]

    @pytest.mark.asyncio
    async def test_asks_by_chunks_of_one_week(self):
        start = datetime(2026, 8, 3, 0, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            market = Market(fake)
            feed = feed_for(fake)
            try:
                await feed.history(start, start + timedelta(days=15))
            finally:
                await feed.aclose()

        spans = [
            (r["toTimestamp"] - r["fromTimestamp"]) // 60_000
            for r in market.bar_requests
        ]
        assert spans == [7 * 1440, 7 * 1440, 1440]

    @pytest.mark.asyncio
    async def test_a_full_chunk_is_split_and_no_minute_is_lost(self):
        # Scénario « troncature » : la réponse pleine est redécoupée (AC-3).
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            market = Market(fake)
            market.fill(start, 40)
            market.cap = 10
            feed = feed_for(fake, max_bars=10)
            try:
                candles = await feed.history(start, start + 40 * M1)
            finally:
                await feed.aclose()

        assert [c.ts_open for c in candles] == [start + i * M1 for i in range(40)]
        assert len(market.bar_requests) > 1

    @pytest.mark.asyncio
    async def test_has_more_also_means_truncated(self):
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            market = Market(fake)
            market.fill(start, 4)
            calls = []

            def first_says_more(payload):
                calls.append(payload)
                kind, body = market._trendbars(payload)
                if len(calls) == 1:
                    return kind, {"trendbar": body["trendbar"][-1:], "hasMore": True}
                return kind, body

            fake.on(Msg.GET_TRENDBARS_REQ, first_says_more)
            feed = feed_for(fake)
            try:
                candles = await feed.history(start, start + 4 * M1)
            finally:
                await feed.aclose()

        assert len(candles) == 4

    @pytest.mark.asyncio
    async def test_missing_minutes_are_never_invented(self):
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            market = Market(fake)
            market.fill(start, 5)
            del market.bars[start + 2 * M1]
            feed = feed_for(fake)
            try:
                candles = await feed.history(start, start + 5 * M1)
            finally:
                await feed.aclose()

        assert start + 2 * M1 not in {c.ts_open for c in candles}
        assert len(candles) == 4

    @pytest.mark.asyncio
    async def test_refuses_times_that_are_not_full_utc_minutes(self):
        async with FakeCTrader() as fake:
            feed = feed_for(fake)
            with pytest.raises(ValueError):
                await feed.history(
                    datetime(2026, 8, 24, 10, 0, 30, tzinfo=UTC),
                    datetime(2026, 8, 24, 11, 0, tzinfo=UTC),
                )


class TestClosedSince:
    @pytest.mark.asyncio
    async def test_never_returns_the_forming_minute(self):
        # Scénario « bougie en formation » (AC-4).
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        now = start + 3 * M1 + timedelta(seconds=3)
        async with FakeCTrader() as fake:
            market = Market(fake)
            market.fill(start, 4)  # la 4e bougie (10h03) se forme encore
            feed = feed_for(fake, clock=lambda: now)
            try:
                candles = await feed.closed_since(start)
            finally:
                await feed.aclose()

        assert [c.ts_open for c in candles] == [start + M1, start + 2 * M1]
        assert market.bar_requests[-1]["toTimestamp"] == int(
            (start + 3 * M1).timestamp() * 1000
        )

    @pytest.mark.asyncio
    async def test_is_empty_while_the_expected_minute_is_not_closed(self):
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            market = Market(fake)
            feed = feed_for(fake, clock=lambda: start + M1 + timedelta(seconds=50))
            try:
                assert await feed.closed_since(start) == []
            finally:
                await feed.aclose()

        assert market.bar_requests == []

    @pytest.mark.asyncio
    async def test_is_empty_when_the_provider_has_nothing_yet(self):
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            Market(fake)
            feed = feed_for(fake, clock=lambda: start + 2 * M1 + timedelta(seconds=3))
            try:
                assert await feed.closed_since(start) == []
            finally:
                await feed.aclose()


class TestConnection:
    @pytest.mark.asyncio
    async def test_unknown_symbol_is_a_clear_api_error(self):
        async with FakeCTrader() as fake:
            Market(fake)
            client = CTraderClient(fake.url, "app-id", "app-secret")
            feed = CTraderFeed(client, ACCOUNT, "GBPJPY", authorize)
            try:
                with pytest.raises(FeedUnavailable, match="GBPJPY") as exc:
                    await feed.history(
                        datetime(2026, 8, 24, 10, 0, tzinfo=UTC),
                        datetime(2026, 8, 24, 10, 5, tzinfo=UTC),
                    )
            finally:
                await feed.aclose()

        assert exc.value.cause == "erreur_api"

    @pytest.mark.asyncio
    async def test_a_symbol_with_more_than_3_digits_is_refused(self):
        async with FakeCTrader() as fake:
            Market(fake, digits=5)
            feed = feed_for(fake)
            try:
                with pytest.raises(FeedUnavailable, match="décimales"):
                    await feed.ensure_ready()
            finally:
                await feed.aclose()

    @pytest.mark.asyncio
    async def test_reconnects_and_reads_the_symbol_again_after_a_drop(self):
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            Market(fake).fill(start, 3)
            feed = feed_for(fake)
            try:
                await feed.history(start, start + 3 * M1)
                await fake.drop_all()
                for _ in range(50):
                    if not feed.client.connected:
                        break
                    await asyncio.sleep(0.01)
                candles = await feed.history(start, start + 3 * M1)
            finally:
                await feed.aclose()

        assert len(candles) == 3
        assert len(fake.of_type(Msg.APPLICATION_AUTH_REQ)) == 2
        assert len(fake.of_type(Msg.SYMBOLS_LIST_REQ)) == 2

    @pytest.mark.asyncio
    async def test_an_auth_refusal_on_bars_reauthorizes_once_then_retries(self):
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            market = Market(fake)
            market.fill(start, 2)
            refused = []

            def refuse_once(payload):
                if not refused:
                    refused.append(payload)
                    return error("CH_CLIENT_NOT_AUTHENTICATED")
                return market._trendbars(payload)

            fake.on(Msg.GET_TRENDBARS_REQ, refuse_once)
            feed = feed_for(fake)
            try:
                candles = await feed.history(start, start + 2 * M1)
            finally:
                await feed.aclose()

        assert len(candles) == 2
        assert len(fake.of_type(Msg.ACCOUNT_AUTH_REQ)) == 2

    @pytest.mark.asyncio
    async def test_a_second_auth_refusal_is_raised(self):
        start = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
        async with FakeCTrader() as fake:
            Market(fake)
            fake.on(
                Msg.GET_TRENDBARS_REQ, lambda p: error("CH_CLIENT_NOT_AUTHENTICATED")
            )
            feed = feed_for(fake)
            try:
                with pytest.raises(FeedAuthError):
                    await feed.history(start, start + 2 * M1)
            finally:
                await feed.aclose()


class TestOpenFeed:
    def base(self, **kwargs) -> Settings:
        values = {
            "database_url": "postgresql://x@localhost/x",
            "ctrader_client_id": "app-id",
            "ctrader_client_secret": "app-secret",
            "ctrader_account_id": ACCOUNT,
        }
        return Settings(**{**values, **kwargs})

    def test_price_source_picks_the_ctrader_adapter(self):
        feed = open_feed(self.base(), engine=None)  # type: ignore[arg-type]

        assert feed.name == "ctrader_icmarkets"
        assert feed.account_id == ACCOUNT
        assert feed.symbol_name == "USDJPY"

    def test_unknown_price_source_is_refused(self):
        with pytest.raises(ConfigMissing, match="PRICE_SOURCE"):
            open_feed(self.base(price_source="oanda"), engine=None)  # type: ignore[arg-type]

    def test_missing_account_id_is_a_clear_message(self):
        with pytest.raises(ConfigMissing, match="CTRADER_ACCOUNT_ID"):
            open_feed(self.base(ctrader_account_id=None), engine=None)  # type: ignore[arg-type]


class TestMaintain:
    def settings(self) -> Settings:
        return Settings(
            database_url="postgresql://x@localhost/x",
            ctrader_client_id="app-id",
            ctrader_client_secret="app-secret",
            ctrader_account_id=ACCOUNT,
        )

    @pytest.mark.asyncio
    async def test_commands_never_renew_the_token(self):
        feed = open_feed(self.settings(), engine=None)  # type: ignore[arg-type]

        await feed.maintain()

        assert not feed.client.connected

    def test_only_the_worker_asks_for_renewal(self):
        feed = open_feed(self.settings(), engine=None, renew_token=True)  # type: ignore[arg-type]

        assert feed._maintain is not None

    @pytest.mark.asyncio
    async def test_maintain_connects_then_runs_the_hook(self):
        seen = []

        async def hook(client):
            seen.append(client.connected)

        async with FakeCTrader() as fake:
            client = CTraderClient(fake.url, "app-id", "app-secret")
            feed = CTraderFeed(client, ACCOUNT, "USDJPY", authorize, maintain=hook)
            try:
                await feed.maintain()
            finally:
                await feed.aclose()

        assert seen == [True]


class TestMalformedAnswers:
    """Revue du 2026-09-29, major 1 : une réponse mal formée est une erreur du
    fournisseur (`FeedUnavailable`, cause `erreur_api`), jamais une exception brute
    qui arrêterait la boucle du flux."""

    START = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "broken",
        [
            {"utcTimestampInMinutes": 29_792_760, "volume": 1},  # pas de `low`
            {"low": 15_917_400, "volume": 1},  # pas d'heure
            {"utcTimestampInMinutes": 29_792_760, "low": "abc"},  # prix illisible
            # Plus haut sous l'ouverture : bougie incohérente.
            {
                "utcTimestampInMinutes": 29_792_760,
                "low": 15_917_400,
                "deltaOpen": 50,
                "deltaHigh": 10,
            },
        ],
    )
    async def test_a_broken_bar_is_an_api_error(self, broken):
        async with FakeCTrader() as fake:
            market = Market(fake)
            market.bars[self.START] = broken
            feed = feed_for(fake)
            try:
                with pytest.raises(FeedUnavailable, match="bougie illisible") as exc:
                    await feed.history(self.START, self.START + 5 * M1)
            finally:
                await feed.aclose()

        assert exc.value.cause == "erreur_api"

    @pytest.mark.asyncio
    async def test_a_broken_symbol_list_is_an_api_error(self):
        async with FakeCTrader() as fake:
            Market(fake)
            fake.on(
                Msg.SYMBOLS_LIST_REQ,
                lambda p: (
                    Msg.SYMBOLS_LIST_RES,
                    {"symbol": [{"symbolName": "USDJPY"}]},
                ),
            )
            feed = feed_for(fake)
            try:
                with pytest.raises(FeedUnavailable) as exc:
                    await feed.history(self.START, self.START + 5 * M1)
            finally:
                await feed.aclose()

        assert exc.value.cause == "erreur_api"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "answer",
        [
            ["pas", "un", "objet"],  # contenu de réponse qui n'est pas un objet
            {"trendbar": ["abc"]},  # bougie qui n'est pas un objet
            {"trendbar": [None]},
        ],
    )
    async def test_an_answer_that_is_not_an_object_is_an_api_error(self, answer):
        # Revue du 2026-09-29 (deuxième passe) : aucune erreur brute ne doit sortir
        # de l'adaptateur, sinon la boucle du flux s'arrête sans ouvrir de coupure.
        async with FakeCTrader() as fake:
            Market(fake)
            fake.on(Msg.GET_TRENDBARS_REQ, lambda p: (Msg.GET_TRENDBARS_RES, answer))
            feed = feed_for(fake)
            try:
                with pytest.raises(FeedUnavailable) as exc:
                    await feed.history(self.START, self.START + 5 * M1)
            finally:
                await feed.aclose()

        assert exc.value.cause == "erreur_api"
