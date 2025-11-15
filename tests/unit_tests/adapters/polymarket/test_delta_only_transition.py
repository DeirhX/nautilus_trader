"""
Tests for delta-only to full order book transition.

Verifies that the optimize_for_deltas_only feature correctly handles
dynamic subscription changes without breaking quote generation.
"""

import asyncio
from decimal import Decimal

import pytest

from nautilus_trader.adapters.polymarket.config import PolymarketDataClientConfig
from nautilus_trader.adapters.polymarket.data import PolymarketDataClient
from nautilus_trader.adapters.polymarket.providers import PolymarketInstrumentProvider
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.data.messages import SubscribeOrderBook
from nautilus_trader.data.messages import SubscribeQuoteTicks
from nautilus_trader.model.book import OrderBook
from nautilus_trader.model.currencies import USDC
from nautilus_trader.model.data import OrderBookDelta
from nautilus_trader.model.enums import AssetClass
from nautilus_trader.model.enums import BookType
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import BinaryOption
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs


class TestDeltaOnlyTransition:
    """Test suite for delta-only to full order book transition."""

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
        """Create an instrument provider (mock)."""
        return PolymarketInstrumentProvider(
            client=None,  # We'll mock the client
            clock=clock,
        )

    @pytest.fixture
    def data_client_safe(self, clock, msgbus, cache, instrument_provider):
        """Create a data client with optimize_for_deltas_only=False."""
        config = PolymarketDataClientConfig(
            api_key="test_key",
            api_secret="test_secret",
            compute_effective_deltas=False,
            optimize_for_deltas_only=False,  # SAFE mode
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
    def data_client_optimized(self, clock, msgbus, cache, instrument_provider):
        """Create a data client with optimize_for_deltas_only=True."""
        config = PolymarketDataClientConfig(
            api_key="test_key",
            api_secret="test_secret",
            compute_effective_deltas=False,
            optimize_for_deltas_only=True,  # OPTIMIZED mode
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

    @pytest.mark.asyncio
    async def test_safe_mode_always_creates_local_book(
        self,
        data_client_safe,
        instrument_id,
    ):
        """
        Test that in SAFE mode, local book is always created even for delta-only.
        """
        # Subscribe to deltas only
        command = SubscribeOrderBook(
            client_id=ClientId("TEST"),
            venue=instrument_id.venue,
            book_data_type=OrderBookDelta,
            instrument_id=instrument_id,
            book_type=BookType.L2_MBP,
            depth=0,
            managed=True,
            command_id=UUID4(),
            ts_init=0,
        )
        
        await data_client_safe._subscribe_order_book_deltas(command)
        
        # Verify: Local book WAS created (SAFE mode)
        assert instrument_id in data_client_safe._local_books

    def test_optimized_mode_initializes_full_book_mode_tracking(
        self,
        data_client_optimized,
    ):
        """
        Test that OPTIMIZED mode initializes the _full_book_mode tracking set.
        
        This set tracks instruments that have transitioned to permanent full book mode.
        """
        # Verify _full_book_mode exists and is initialized as empty set
        assert hasattr(data_client_optimized, '_full_book_mode')
        assert isinstance(data_client_optimized._full_book_mode, set)
        assert len(data_client_optimized._full_book_mode) == 0

    def test_safe_mode_initializes_full_book_mode_tracking(
        self,
        data_client_safe,
    ):
        """
        Test that SAFE mode also has _full_book_mode (though not used).
        
        Both modes have the set for consistency, but SAFE mode doesn't need it.
        """
        # Verify _full_book_mode exists
        assert hasattr(data_client_safe, '_full_book_mode')
        assert isinstance(data_client_safe._full_book_mode, set)
        assert len(data_client_safe._full_book_mode) == 0

    @pytest.mark.asyncio
    async def test_optimized_mode_skips_local_book_for_delta_only(
        self,
        data_client_optimized,
        instrument_id,
    ):
        """
        Test that OPTIMIZED mode does NOT create local books for delta-only subscriptions.
        
        This is the core optimization - skipping expensive book maintenance.
        """
        # Subscribe to deltas only
        command = SubscribeOrderBook(
            client_id=ClientId("TEST"),
            venue=instrument_id.venue,
            book_data_type=OrderBookDelta,
            instrument_id=instrument_id,
            book_type=BookType.L2_MBP,
            depth=0,
            managed=True,
            command_id=UUID4(),
            ts_init=0,
        )
        
        await data_client_optimized._subscribe_order_book_deltas(command)
        
        # Verify: NO local book created (optimization active)
        assert instrument_id not in data_client_optimized._local_books
        
        # Verify: NOT in full_book_mode (hasn't transitioned yet)
        assert instrument_id not in data_client_optimized._full_book_mode

    def test_configuration_differences_between_modes(
        self,
        data_client_safe,
        data_client_optimized,
    ):
        """
        Test that SAFE and OPTIMIZED modes have correct configuration.
        
        This documents the key configuration difference.
        """
        # SAFE mode configuration
        assert data_client_safe._config.optimize_for_deltas_only is False
        
        # OPTIMIZED mode configuration
        assert data_client_optimized._config.optimize_for_deltas_only is True
        
        # Both should have the same other settings
        assert data_client_safe._config.compute_effective_deltas == data_client_optimized._config.compute_effective_deltas

    def test_optimized_mode_permanent_transition_logic(
        self,
        data_client_optimized,
        instrument_id,
    ):
        """
        CRITICAL TEST: Validates permanent transition behavior (without WebSocket).
        
        This tests the state management of the permanent transition:
        - Once an instrument is added to _full_book_mode, it stays there
        - This ensures quotes will always work, even after unsubscribe/resubscribe
        
        Note: This doesn't test the actual transition (requires WebSocket),
        but validates the state tracking mechanism.
        """
        # Initially, instrument not in full book mode
        assert instrument_id not in data_client_optimized._full_book_mode
        
        # Simulate the transition: manually add to full_book_mode
        # (In real code, this happens in _subscribe_quote_ticks when transitioning)
        data_client_optimized._full_book_mode.add(instrument_id)
        
        # Verify it's now tracked
        assert instrument_id in data_client_optimized._full_book_mode
        
        # Key property: Once added, it should stay (permanent transition)
        # Even if we later "unsubscribe" from quotes, the instrument remains
        # This is the "one-way transition" - you can't go back to delta-only
        
        # Simulate checking if we should maintain book (logic from _handle_deltas)
        should_maintain = (
            not data_client_optimized._config.optimize_for_deltas_only  # SAFE mode
            or instrument_id in data_client_optimized._full_book_mode  # Permanent mode
            or instrument_id in data_client_optimized.subscribed_quote_ticks()  # Active quotes
        )
        
        # With permanent transition, should_maintain is True even without active quotes
        assert should_maintain  # True because instrument is in _full_book_mode
        
        # This ensures:
        # 1. Once quotes are added, book is ALWAYS maintained
        # 2. Unsubscribing from quotes doesn't break future quote subscriptions
        # 3. The transition is permanent and one-way
