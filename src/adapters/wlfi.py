"""WLFI Markets (World Liberty Financial / Dolomite) adapter."""

from typing import Any, Dict, List, Optional
import requests

from src.schema import Row


# WLFI Markets TRPC endpoints
TOKENS_URL = "https://api-markets.worldlibertyfinancial.com/trpc/dolomite.getTokens?input=%7B%22json%22%3A%7B%22chainId%22%3A1%7D%7D"
RATES_URL = "https://api-markets.worldlibertyfinancial.com/trpc/dolomite.getInterestRates?input=%7B%22json%22%3A%7B%22chainId%22%3A1%7D%7D"

PROTOCOL_NAME = "WLFI Markets"
TARGET_SYMBOL = "USD1"

# Minimal browser-like headers
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


def _trpc_json(url: str, timeout: float) -> Any:
    """Fetch JSON from a tRPC endpoint with proper unwrapping."""
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, list):
        payload = payload[0]

    return payload["result"]["data"]["json"]


def _format_percent(fraction: float) -> str:
    """Format a fraction (0.xx) as a percent string with 2 decimals."""
    return f"{fraction * 100:.2f}%"


def fetch_row(timeout: float = 20.0, debug: bool = False) -> Row:
    """Fetch USD1 market data from WLFI Markets."""
    try:
        tokens: List[Dict] = _trpc_json(TOKENS_URL, timeout)
        rates: List[Dict] = _trpc_json(RATES_URL, timeout)

        rate_by_market: Dict[int, Dict] = {}
        for r in rates:
            token_info = r.get("token")
            if isinstance(token_info, dict):
                mid = token_info.get("marketId")
                if mid is not None:
                    rate_by_market[mid] = r

        usd1_token: Optional[Dict] = None
        market_id: Optional[int] = None

        for t in tokens:
            symbol = (t.get("symbol") or "").upper()
            if symbol == TARGET_SYMBOL:
                usd1_token = t
                market_id = t.get("marketId")
                break

        if usd1_token is None or market_id is None:
            return Row(
                protocol=PROTOCOL_NAME,
                total_supplied=None,
                supply_rate="N/A",
                total_borrowed=None,
                borrow_rate="N/A",
            )

        rate_obj = rate_by_market.get(market_id)
        if rate_obj is None:
            return Row(
                protocol=PROTOCOL_NAME,
                total_supplied=_to_float(usd1_token.get("supplyLiquidity")),
                supply_rate="N/A",
                total_borrowed=_to_float(usd1_token.get("borrowLiquidity")),
                borrow_rate="N/A",
            )

        supplied = _to_float(usd1_token.get("supplyLiquidity"))
        borrowed = _to_float(usd1_token.get("borrowLiquidity"))
        base_supply = _to_float(rate_obj.get("supplyInterestRate"))
        borrow_rate_val = _to_float(rate_obj.get("borrowInterestRate"))

        incentive: float = 0.0
        outside_parts = rate_obj.get("outsideSupplyInterestRateParts", [])
        if isinstance(outside_parts, list):
            for part in outside_parts:
                if not isinstance(part, dict):
                    continue
                label = (part.get("label") or "").lower()
                claim_url = (part.get("rewardClaimUrl") or "").lower()
                interest_rate = _to_float(part.get("interestRate"))

                if interest_rate is not None:
                    is_merkl = "merkl" in label or "merkl" in claim_url
                    is_wlfi = "wlfi rewards" in label
                    if is_merkl or is_wlfi:
                        incentive += interest_rate

        if base_supply is not None:
            total_supply_rate = base_supply + incentive
            if incentive > 0:
                supply_rate_str = (
                    f"{_format_percent(total_supply_rate)} "
                    f"(base {_format_percent(base_supply)} + inc {_format_percent(incentive)})"
                )
            else:
                supply_rate_str = _format_percent(base_supply)
        else:
            supply_rate_str = "N/A"

        if borrow_rate_val is not None:
            borrow_rate_str = _format_percent(borrow_rate_val)
        else:
            borrow_rate_str = "N/A"

        return Row(
            protocol=PROTOCOL_NAME,
            total_supplied=supplied,
            supply_rate=supply_rate_str,
            total_borrowed=borrowed,
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
