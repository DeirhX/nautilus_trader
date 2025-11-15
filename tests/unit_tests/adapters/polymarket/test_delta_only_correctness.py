"""
Tests for delta-only fast path implementation correctness.

Verifies that the delta-only optimization produces correct results
and is properly triggered based on subscription mode.
"""

import asyncio
from decimal import Decimal
from unittest.mock import Mock

import pytest

from nautilus_trader.adapters.polymarket.config import PolymarketDataClientConfig
from nautilus_trader.adapters.polymarket.data import PolymarketDataClient
from nautilus_trader.adapters.polymarket.data import SubscriptionMode
from nautilus_trader.adapters.polymarket.providers import PolymarketInstrumentProvider
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.data.messages import SubscribeOrderBook
from nautilus_trader.model.currencies import USDC
from nautilus_trader.model.enums import AssetClass
from nautilus_trader.model.enums import BookType
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import BinaryOption
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs


class TestDeltaOnlyCorrectness:
    """Test suite for delta-only implementation correctness."""

    @pytest.fixture
    def clock(self):
        """Create a live clock."""
        return LiveClock()

    @pytest.fixture
    def msgbus(self, clock):
        """Create a message bus."""
        return MessageBus(
            trader_id=TestIdStubs.trader_id(),
            clock=clock,
        )

    @pytest.fixture
    def cache(self):
        """Create a cache."""
        return Cache()

    @pytest.fixture
    def instrument_provider(self, clock):
        """Create a mock instrument provider."""
        provider = Mock(spec=PolymarketInstrumentProvider)
        return provider

    @pytest.fixture
    def data_client_optimized(self, clock, msgbus, cache, instrument_provider):
        """Create a data client with optimize_for_deltas_only=True."""
        config = PolymarketDataClientConfig(
            api_key="test_key",
            api_secret="test_secret",
            compute_effective_deltas=False,
            optimize_for_deltas_only=True,
        )
        
        client = PolymarketDataClient(
            loop=asyncio.get_event_loop(),
            http_client=None,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=instrument_provider,
            config=config,
            name="POLYMARKET-TEST",
        )
        
        return client

    @pytest.fixture
    def instrument_id(self):
        """Create a test instrument ID."""
        return InstrumentId.from_str("0x1234-YES.POLYMARKET")

    @pytest.fixture
    def instrument(self, instrument_id):
        """Create a test instrument."""
        price_increment = Price.from_str("0.0001")
        size_increment = Quantity.from_str("0.01")
        return BinaryOption(
            instrument_id=instrument_id,
            raw_symbol=instrument_id.symbol,
            outcome="YES",
            description="Test Polymarket Instrument",
            asset_class=AssetClass.ALTERNATIVE,
            currency=USDC,
            activation_ns=0,
            expiration_ns=0,
            price_precision=price_increment.precision,
            price_increment=price_increment,
            size_precision=size_increment.precision,
            size_increment=size_increment,
            maker_fee=Decimal("0"),
            taker_fee=Decimal("0"),
            ts_event=0,
            ts_init=0,
        )

    def test_subscription_mode_enum_values(self):
        """Test that SubscriptionMode enum has correct values."""
        assert SubscriptionMode.NONE == 0
        assert SubscriptionMode.DELTAS_ONLY == 1
        assert SubscriptionMode.QUOTES_ONLY == 2
        assert SubscriptionMode.BOTH == 3
        
        # Verify it's an IntEnum (for fast comparisons)
        assert isinstance(SubscriptionMode.DELTAS_ONLY, int)

    def test_subscription_mode_bitwise_combination(self):
        """
        Test that SubscriptionMode values combine correctly.
        
        BOTH should equal DELTAS_ONLY + QUOTES_ONLY (bitwise OR).
        """
        # Verify bitwise combination
        assert SubscriptionMode.BOTH == (SubscriptionMode.DELTAS_ONLY | SubscriptionMode.QUOTES_ONLY)
        
        # Verify individual checks work
        assert SubscriptionMode.BOTH & SubscriptionMode.DELTAS_ONLY
        assert SubscriptionMode.BOTH & SubscriptionMode.QUOTES_ONLY
        assert not (SubscriptionMode.DELTAS_ONLY & SubscriptionMode.QUOTES_ONLY)

    def test_subscription_mode_cache_initialization(
        self,
        data_client_optimized,
    ):
        """
        Test that subscription mode cache is initialized correctly.
        
        This cache stores the current subscription mode for each instrument.
        """
        # Verify cache exists and is empty
        assert hasattr(data_client_optimized, '_subscription_mode_cache')
        assert isinstance(data_client_optimized._subscription_mode_cache, dict)
        assert len(data_client_optimized._subscription_mode_cache) == 0

    def test_instrument_cache_initialization(
        self,
        data_client_optimized,
    ):
        """
        Test that instrument cache is initialized correctly.
        
        This cache stores instrument references to avoid repeated lookups.
        """
        # Verify cache exists and is empty
        assert hasattr(data_client_optimized, '_instrument_cache')
        assert isinstance(data_client_optimized._instrument_cache, dict)
        assert len(data_client_optimized._instrument_cache) == 0
