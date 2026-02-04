"""Kamino adapter for USD1 vault and lending markets."""

from typing import Any, Dict, List, Optional
import requests

from src.schema import Row


BASE = "https://api.kamino.finance"
VAULT = "2eCcHyUfFmiLX5RnNY21Qfndqww7TmwaKBgNXX5Unu7o"

MARKETS = {
    "Main Market": "7u3HeHxYDLhnCoErrtycNokbQYbWGzLs6JSDqGAv5PfF",
    "Maple Market": "6WEGfej9B9wjxRs6t4BYpb9iCXd8CpTpJ8fVSNzHCC5y",
    "JLP Market": "DxXdAyU3kCjnyggvHmY5nAwg5cRbbmdyX3npfDMjjMek",
}

PROTOCOL_NAME = "Kamino"
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


def fetch_row(timeout: float = 20.0, debug: bool = False) -> Row:
    """Fetch USD1 market data from Kamino."""
    try:
        vault_url = f"{BASE}/kvaults/vaults/{VAULT}/metrics"
        resp = requests.get(vault_url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        m = resp.json()

        tokens_available = _to_float(m.get("tokensAvailableUsd")) or 0.0
        tokens_invested = _to_float(m.get("tokensInvestedUsd")) or 0.0
        total_supplied_usd = tokens_available + tokens_invested

        lend_apy = (_to_float(m.get("apy")) or 0.0) * 100
        wlfi_apy = (_to_float(m.get("apyFarmRewards")) or 0.0) * 100
        kmno_apy = (_to_float(m.get("apyIncentives")) or 0.0) * 100
        combined_apy = lend_apy + wlfi_apy + kmno_apy

        supply_rate_str = (
            f"{combined_apy:.2f}% "
            f"(lend {lend_apy:.2f}% + WLFI {wlfi_apy:.2f}% + KMNO {kmno_apy:.2f}%)"
        )

        tot_borrow = 0.0

        for market_name, market_pk in MARKETS.items():
            reserves_url = f"{BASE}/kamino-market/{market_pk}/reserves/metrics"
            try:
                resp = requests.get(reserves_url, headers=HEADERS, timeout=timeout)
                resp.raise_for_status()
                reserves: List[Dict] = resp.json()

                for r in reserves:
                    if isinstance(r, dict) and r.get("liquidityToken") == TARGET_SYMBOL:
                        tb = _to_float(r.get("totalBorrow")) or 0.0
                        tot_borrow += tb
                        break
            except requests.RequestException:
                continue

        borrow_rate_str = f"{lend_apy:.2f}%"

        return Row(
            protocol=PROTOCOL_NAME,
            total_supplied=total_supplied_usd,
            supply_rate=supply_rate_str,
            total_borrowed=tot_borrow,
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
