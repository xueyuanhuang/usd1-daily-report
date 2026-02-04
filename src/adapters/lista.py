"""Lista (BSC) adapter for USD1 vault metrics."""

from typing import Any, Dict, List, Optional

from src.schema import Row
from src.util.http import fetch_json


VAULT_LIST_URL = "https://api.lista.org/api/moolah/vault/list"
VAULT_ALLOCATION_URL = "https://api.lista.org/api/moolah/vault/allocation"

PROTOCOL_NAME = "Lista"
TARGET_VAULT_ADDRESS = "0xfa27f172e0b6ebcef9c51abf817e2cb142fbe627"
TARGET_ASSET_SYMBOL = "USD1"

TOP_N_MARKETS = 5


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


def _find_usd1_vault(vaults: List[Dict], debug: bool = False) -> Optional[Dict]:
    """Find the USD1 vault from the vault list."""
    for vault in vaults:
        address = (vault.get("address") or "").lower()
        asset_symbol = (vault.get("assetSymbol") or "").upper()

        if address == TARGET_VAULT_ADDRESS.lower():
            return vault
        if asset_symbol == TARGET_ASSET_SYMBOL:
            return vault

    return None


def _compute_borrow_rate_range(markets: List[Dict], top_n: int = TOP_N_MARKETS) -> str:
    """Compute the borrow rate range from top N markets by allocation."""
    if not markets:
        return "N/A"

    parsed = []
    for m in markets:
        allocation = _to_float(m.get("allocation"))
        borrow_rate = _to_float(m.get("borrowRate"))

        if allocation is not None and borrow_rate is not None:
            parsed.append({
                "allocation": allocation,
                "borrow_rate": borrow_rate,
            })

    if not parsed:
        return "N/A"

    parsed.sort(key=lambda x: x["allocation"], reverse=True)
    top_markets = parsed[:top_n]
    borrow_rates = [m["borrow_rate"] for m in top_markets]

    if not borrow_rates:
        return "N/A"

    min_rate = min(borrow_rates)
    max_rate = max(borrow_rates)

    return f"{min_rate * 100:.2f}%-{max_rate * 100:.2f}%"


def fetch_row(timeout: float = 20.0, debug: bool = False) -> Row:
    """Fetch USD1 vault data from Lista."""
    try:
        vault_params = "?sort=depositsUsd&order=desc&chain=bsc"
        vault_data = fetch_json(VAULT_LIST_URL + vault_params, timeout=timeout, debug=debug)

        vaults = vault_data.get("data", {}).get("list", [])
        usd1_vault = _find_usd1_vault(vaults, debug=debug)

        if usd1_vault is None:
            return Row(
                protocol=PROTOCOL_NAME,
                total_supplied=None,
                supply_rate="N/A",
                total_borrowed=None,
                borrow_rate="N/A",
            )

        vault_address = usd1_vault.get("address", TARGET_VAULT_ADDRESS)
        deposits = _to_float(usd1_vault.get("deposits"))
        apy = _to_float(usd1_vault.get("apy"))
        utilization = _to_float(usd1_vault.get("utilization"))

        total_borrowed: Optional[float] = None
        if deposits is not None and utilization is not None:
            total_borrowed = deposits * utilization

        supply_rate_str = _format_percent(apy) if apy is not None else "N/A"

        allocation_params = f"?address={vault_address}&chain=bsc"
        allocation_data = fetch_json(
            VAULT_ALLOCATION_URL + allocation_params,
            timeout=timeout,
            debug=debug,
        )

        markets = allocation_data.get("data", {}).get("list", [])
        borrow_rate_str = _compute_borrow_rate_range(markets, TOP_N_MARKETS)

        return Row(
            protocol=PROTOCOL_NAME,
            total_supplied=deposits,
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
