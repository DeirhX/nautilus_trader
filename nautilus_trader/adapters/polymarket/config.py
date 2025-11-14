# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2025 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

from nautilus_trader.adapters.polymarket.common.constants import POLYMARKET_VENUE
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.config import PositiveFloat
from nautilus_trader.config import PositiveInt
from nautilus_trader.model.identifiers import Venue


class PolymarketDataClientConfig(LiveDataClientConfig, frozen=True):
    """
    Configuration for ``PolymarketDataClient`` instances.

    Parameters
    ----------
    venue : Venue, default POLYMARKET_VENUE
        The venue for the client.
    private_key : str, optional
        The private key for the wallet on the **Polygon** network.
        If ``None`` then will source the `POLYMARKET_PK` environment variable.
    signature_type : int, default 0 (EOA)
        The Polymarket signature type:
        - 0: EOA (Externally Owned Account)
        - 1: Email/Magic Wallet Proxy
        - 2: Browser Wallet Proxy
    funder : str, optional
        The wallet address (public key) on the **Polygon** network used for funding USDC.
        If ``None`` then will source the `POLYMARKET_FUNDER` environment variable.
    api_key : str, optional
        The Polymarket API key.
        If ``None`` then will source the `POLYMARKET_API_KEY` environment variable.
    api_secret : str, optional
        The Polymarket API secret.
        If ``None`` then will source the `POLYMARKET_API_SECRET` environment variable.
    passphrase : str, optional
        The Polymarket API passphrase.
        If ``None`` then will source the `POLYMARKET_PASSPHRASE` environment variable.
    base_url_http : str, optional
        The HTTP client custom endpoint override.
    base_url_ws : str, optional
        The WebSocket client custom endpoint override.
    ws_connection_initial_delay_secs: PositiveFloat, default 5
        The delay (seconds) prior to the first websocket connection to allow initial subscriptions to arrive.
    ws_connection_delay_secs : PositiveFloat, default 0.1
        The delay (seconds) prior to making a new websocket connection to allow non-initial subscriptions to arrive.
    update_instruments_interval_mins: PositiveInt or None, default 60
        The interval (minutes) between updating Polymarket instruments.
    compute_effective_deltas : bool, default False
        If True, computes effective deltas by comparing old and new order book states,
        reducing snapshot size. This takes ~1 millisecond, so is not recommended for latency-sensitive strategies.
    drop_quotes_missing_side : bool, default True
        If True, drops QuoteTick messages when bid or ask prices are missing (can occur near market resolution).
        If False, uses boundary prices (0.001/0.999) with zero volume for missing sides.
    optimize_for_deltas_only : bool, default True
        Controls whether to skip local book maintenance for delta-only subscriptions.
        
        If True (OPTIMIZED mode):
        - Skips local book maintenance for delta-only subscriptions (~84% faster: 0.62ms → 0.1ms)
        - Trade-off: Local book will be EMPTY if you later add quote subscriptions mid-session
        - Use when: Subscriptions are stable and never change during session (e.g., pure arbitrage)
        
        If False (SAFE mode):
        - Always maintains local books for all subscription types (~5-10% slower for delta-only)
        - Safe for: Dynamic subscription changes (can switch delta-only → quotes anytime)
        - Use when: Strategy dynamically subscribes/unsubscribes to different data types
        
        Note: Book maintenance overhead is small (~0.05ms per update) but adds up at high frequency.
        For 10k updates/sec, SAFE mode uses ~500ms more CPU/sec vs OPTIMIZED mode.
    skip_quote_deduplication : bool, default False
        If True, skips the duplicate quote check (always publishes).
        Reduces latency by ~0.05-0.1ms per quote but increases message bus load.
        Enable for ultra-low-latency arbitrage strategies (only applies to quote subscriptions).

    """

    venue: Venue = POLYMARKET_VENUE
    private_key: str | None = None
    signature_type: int = 0
    funder: str | None = None
    api_key: str | None = None
    api_secret: str | None = None
    passphrase: str | None = None
    base_url_http: str | None = None
    base_url_ws: str | None = None
    ws_connection_initial_delay_secs: PositiveFloat = 5
    ws_connection_delay_secs: PositiveFloat = 0.1
    update_instruments_interval_mins: PositiveInt | None = 60
    compute_effective_deltas: bool = False
    drop_quotes_missing_side: bool = True
    optimize_for_deltas_only: bool = True
    skip_quote_deduplication: bool = False


class PolymarketExecClientConfig(LiveExecClientConfig, frozen=True):
    """
    Configuration for ``PolymarketExecutionClient`` instances.

    Parameters
    ----------
    venue : Venue, default POLYMARKET_VENUE
        The venue for the client.
    private_key : str, optional
        The private key for the wallet on the **Polygon** network.
        If ``None`` then will source the `POLYMARKET_PK` environment variable.
    signature_type : int, default 0 (EOA)
        The Polymarket signature type:
        - 0: EOA (Externally Owned Account)
        - 1: Email/Magic Wallet Proxy
        - 2: Browser Wallet Proxy
    funder : str, optional
        The wallet address (public key) on the **Polygon** network used for funding USDC.
        If ``None`` then will source the `POLYMARKET_FUNDER` environment variable.
    api_key : str, optional
        The Polymarket API key.
        If ``None`` then will source the `POLYMARKET_API_KEY` environment variable.
    api_secret : str, optional
        The Polymarket API secret.
        If ``None`` then will source the `POLYMARKET_API_SECRET` environment variable.
    passphrase : str, optional
        The Polymarket API passphrase.
        If ``None`` then will source the `POLYMARKET_PASSPHRASE` environment variable.
    base_url_http : str, optional
        The HTTP client custom endpoint override.
    base_url_ws : str, optional
        The WebSocket client custom endpoint override.
    max_retries : PositiveInt, optional
        The maximum number of times a submit or cancel order request will be retried.
    retry_delay_initial_ms : PositiveInt, optional
        The initial delay (milliseconds) between retries. Short delays with frequent retries may result in account bans.
    retry_delay_max_ms : PositiveInt, optional
        The maximum delay (milliseconds) between retries.
    generate_order_history_from_trades : bool, default False
        If True, uses trades history to generate reports for orders which are no longer active.
        The Polymarket API only returns active orders and trades.
        This feature is experimental and is not currently recommended (leave set to False).
    log_raw_ws_messages : bool, default False
        If raw websocket messages should be logged with INFO level.
        Note: there will be a performance penalty parsing the JSON without an efficient msgspec decoder.
    ack_timeout_secs : PositiveFloat, default 5.0
        The timeout (seconds) to wait for order/trade acknowledgment from cache.
    use_data_api : bool, default False
        Determines which API to use for fetching user positions:
        - True: Data API (experimental) - efficient for large workloads, fewer API calls
        - False: CLOB API (stable, default) - balance/allowance endpoint, one request per instrument

    """

    venue: Venue = POLYMARKET_VENUE
    private_key: str | None = None
    signature_type: int = 0
    funder: str | None = None
    api_key: str | None = None
    api_secret: str | None = None
    passphrase: str | None = None
    base_url_http: str | None = None
    base_url_ws: str | None = None
    max_retries: PositiveInt | None = None
    retry_delay_initial_ms: PositiveInt | None = None
    retry_delay_max_ms: PositiveInt | None = None
    generate_order_history_from_trades: bool = False
    log_raw_ws_messages: bool = False
    ack_timeout_secs: PositiveFloat = 5.0
    use_data_api: bool = False
