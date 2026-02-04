"""Stablecoin data fetching from DefiLlama."""

import time
from typing import Any

import requests


STABLECOINS_API_URL = "https://stablecoins.llama.fi/stablecoins"
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 2

DEFAULT_TOKENS = ["USDT", "USDC", "USD1", "U"]


def fetch_with_retry(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
) -> dict[str, Any]:
    """Fetch JSON from URL with exponential backoff retry."""
    last_exception = None

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            last_exception = e
            if attempt < retries - 1:
                wait_time = backoff_factor ** attempt
                time.sleep(wait_time)

    raise last_exception


def fetch_stablecoins() -> list[dict[str, Any]]:
    """Fetch all stablecoins data from DefiLlama API."""
    data = fetch_with_retry(STABLECOINS_API_URL)
    return data.get("peggedAssets", [])


def get_stablecoin_by_symbol(
    stablecoins: list[dict[str, Any]], symbol: str
) -> dict[str, Any] | None:
    """Find a stablecoin by its symbol (case-insensitive)."""
    symbol_upper = symbol.upper()
    for coin in stablecoins:
        if coin.get("symbol", "").upper() == symbol_upper:
            return coin
    return None


def extract_circulating_value(circulating_data: dict[str, Any] | None) -> float | None:
    """Extract the peggedUSD value from circulating data."""
    if circulating_data is None:
        return None

    if isinstance(circulating_data, dict):
        return circulating_data.get("peggedUSD")

    if isinstance(circulating_data, (int, float)):
        return float(circulating_data)

    return None


def calculate_percent_change(current: float | None, previous: float | None) -> float | None:
    """Calculate percentage change between two values."""
    if current is None or previous is None:
        return None
    if previous == 0:
        return None

    change = (current - previous) / previous * 100
    return round(change, 2)


def parse_stablecoin_metrics(coin_data: dict[str, Any]) -> dict[str, Any]:
    """Parse stablecoin data and compute metrics."""
    symbol = coin_data.get("symbol", "UNKNOWN")

    current = extract_circulating_value(coin_data.get("circulating"))
    prev_day = extract_circulating_value(coin_data.get("circulatingPrevDay"))
    prev_week = extract_circulating_value(coin_data.get("circulatingPrevWeek"))

    change_1d = calculate_percent_change(current, prev_day)
    change_7d = calculate_percent_change(current, prev_week)

    market_cap = int(current) if current is not None else None

    return {
        "symbol": symbol,
        "market_cap_usd": market_cap,
        "change_1d_pct": change_1d,
        "change_7d_pct": change_7d,
    }


def format_pct(value: float | None) -> str:
    """Format a numeric percent value as a string with % sign."""
    if value is None:
        return ""
    return f"{value:.2f}%"


def format_usd_compact(value: int | None) -> str:
    """Format USD value in compact notation with $ prefix."""
    if value is None:
        return ""

    if value >= 1_000_000_000:
        billions = value / 1_000_000_000
        return f"${billions:.3f}B"
    elif value >= 1_000_000:
        millions = value / 1_000_000
        return f"${millions:.2f}M"
    else:
        return f"${value}"


def get_stablecoin_data(tokens: list[str] | None = None) -> list[dict[str, str]]:
    """Fetch and format stablecoin data for specified tokens."""
    if tokens is None:
        tokens = DEFAULT_TOKENS

    stablecoins = fetch_stablecoins()
    rows = []

    for token in tokens:
        coin_data = get_stablecoin_by_symbol(stablecoins, token)

        if coin_data is None:
            continue

        metrics = parse_stablecoin_metrics(coin_data)

        if metrics["market_cap_usd"] is None:
            continue

        row = {
            "Token": metrics["symbol"],
            "1D Change": format_pct(metrics["change_1d_pct"]),
            "7D Change": format_pct(metrics["change_7d_pct"]),
            "Market Cap": format_usd_compact(metrics["market_cap_usd"]),
        }
        rows.append(row)

    return rows
