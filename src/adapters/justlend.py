"""JustLend adapter."""

from typing import Optional, Any

from src.schema import Row
from src.util.http import fetch_json
from src.util.parse import normalize_rate, format_rate, safe_get


API_URL = "https://labc.ablesdxd.link/justlend/yieldInfos?config=TE2RzoSV3wFK99w6J9UnnZ4vLfXYoxvRwP$0$14,TXJgMdjVX5dKiQaUi9QobwNxtSQaFqccvd$0$14,TL5x9MtSnDy537FXKx53yAaHRRNdg9TkkA$0$14,TGBr8uh9jBVHJhhkwSJvQN2ZAKzVkxDmno$0$14,TRg6MnpsFXc82ymUPgf5qbj59ibxiEDWvv$0$14,TLeEu311Cbw63BcmMHDgDLu7fnk9fqGcqT$0$14,TWQhCXaWz4eHK4Kd1ErSDHjMFPoPc9czts$0$14,TUY54PVeH6WCcYCd6ZXXoBDsHytN9V5PXt$0$14,TR7BUFRQeq1w5jAZf1FKx85SHuX6PfMqsV$0$14,TFpPyDCKvNFgos3g3WVsAqMrdqhB81JXHE$0$14"

PROTOCOL_NAME = "JustLend"
TARGET_SYMBOL = "USD1"


def fetch_row(timeout: float = 20.0, debug: bool = False) -> Row:
    """Fetch USD1 market data from JustLend."""
    data = fetch_json(API_URL, timeout=timeout, debug=debug)

    asset_list = safe_get(data, "data", "assetList", default=[])
    usd1_market = None

    for asset in asset_list:
        if isinstance(asset, dict):
            symbol = asset.get("collateralSymbol", "").upper()
            if symbol == TARGET_SYMBOL:
                usd1_market = asset
                break

    if usd1_market is None:
        return Row(
            protocol=PROTOCOL_NAME,
            total_supplied=None,
            supply_rate="N/A",
            total_borrowed=None,
            borrow_rate="N/A",
        )

    total_supplied = _extract_usd_amount(usd1_market, "depositedUSD")
    total_borrowed = _extract_usd_amount(usd1_market, "borrowedUSD")
    supply_rate_str = _extract_supply_rate(usd1_market)
    borrow_rate_str = _extract_borrow_rate(usd1_market)

    return Row(
        protocol=PROTOCOL_NAME,
        total_supplied=total_supplied,
        supply_rate=supply_rate_str,
        total_borrowed=total_borrowed,
        borrow_rate=borrow_rate_str,
    )


def _extract_usd_amount(market: dict, key: str) -> Optional[float]:
    """Extract USD amount from string field."""
    value = market.get(key)
    if value is not None:
        try:
            return float(value)
        except (ValueError, TypeError):
            pass
    return None


def _extract_supply_rate(market: dict) -> str:
    """Extract and format supply rate (depositedAPY)."""
    base_rate = None
    value = market.get("depositedAPY")
    if value is not None:
        base_rate = normalize_rate(value)

    incentive_rate = None
    inc_value = market.get("underlyingIncrementApy")
    if inc_value is not None and inc_value != "0":
        incentive_rate = normalize_rate(inc_value)

    return format_rate(base_rate, incentive_rate, is_borrow=False)


def _extract_borrow_rate(market: dict) -> str:
    """Extract and format borrow rate (borrowedAPY)."""
    base_rate = None
    value = market.get("borrowedAPY")
    if value is not None:
        base_rate = normalize_rate(value)

    return format_rate(base_rate, None, is_borrow=False)
