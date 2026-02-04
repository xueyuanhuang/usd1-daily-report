"""Echelon (Aptos) adapter."""

from typing import Any, Dict, List, Optional
import requests

from src.schema import Row


API_URL = "https://app.echelon.market/api/markets?network=aptos_mainnet"

PROTOCOL_NAME = "Echelon"
TARGET_SYMBOL = "USD1"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


def _to_float(val: Any) -> Optional[float]:
    """Safely convert a value to float."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _format_percent(fraction: float) -> str:
    """Format a fraction (0.xx) as a percent string with 2 decimals."""
    return f"{fraction * 100:.2f}%"


def fetch_row(timeout: float = 20.0, debug: bool = False) -> Row:
    """Fetch USD1 market data from Echelon."""
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        root = response.json()
        data = root["data"]

        market_stats_raw = data.get("marketStats", [])
        market_stats: Dict[str, Dict] = {}
        for pair in market_stats_raw:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                k, v = pair
                market_stats[k] = v

        assets = data.get("assets", [])
        usd1_asset: Optional[Dict] = None
        for asset in assets:
            if isinstance(asset, dict) and asset.get("symbol") == TARGET_SYMBOL:
                usd1_asset = asset
                break

        if usd1_asset is None:
            return Row(
                protocol=PROTOCOL_NAME,
                total_supplied=None,
                supply_rate="N/A",
                total_borrowed=None,
                borrow_rate="N/A",
            )

        stats_key = usd1_asset.get("faAddress") or usd1_asset.get("address")
        stats = market_stats.get(stats_key)

        if stats is None:
            return Row(
                protocol=PROTOCOL_NAME,
                total_supplied=None,
                supply_rate="N/A",
                total_borrowed=None,
                borrow_rate="N/A",
            )

        total_supplied = _to_float(stats.get("totalShares"))
        total_borrowed = _to_float(stats.get("totalLiability"))

        lend_apr = _to_float(usd1_asset.get("supplyApr")) or 0.0
        borrow_apr = _to_float(usd1_asset.get("borrowApr")) or 0.0

        farming = usd1_asset.get("farmingApr") or {}
        if not isinstance(farming, dict):
            farming = {}

        inc_supply = sum(
            _to_float(i.get("apr")) or 0.0
            for i in (farming.get("supply") or [])
            if isinstance(i, dict)
        )
        inc_borrow = sum(
            _to_float(i.get("apr")) or 0.0
            for i in (farming.get("borrow") or [])
            if isinstance(i, dict)
        )

        supply_total = lend_apr + inc_supply
        borrow_effective = borrow_apr - inc_borrow

        if inc_supply > 0:
            supply_rate_str = (
                f"{_format_percent(supply_total)} "
                f"(base {_format_percent(lend_apr)} + inc {_format_percent(inc_supply)})"
            )
        else:
            supply_rate_str = _format_percent(lend_apr)

        if inc_borrow > 0:
            borrow_rate_str = (
                f"{_format_percent(borrow_effective)} "
                f"(borrow {_format_percent(borrow_apr)} - inc {_format_percent(inc_borrow)})"
            )
        else:
            borrow_rate_str = _format_percent(borrow_apr)

        return Row(
            protocol=PROTOCOL_NAME,
            total_supplied=total_supplied,
            supply_rate=supply_rate_str,
            total_borrowed=total_borrowed,
            borrow_rate=borrow_rate_str,
        )

    except Exception:
        return Row(
            protocol=PROTOCOL_NAME,
            total_supplied=None,
            supply_rate="N/A",
            total_borrowed=None,
            borrow_rate="N/A",
        )
