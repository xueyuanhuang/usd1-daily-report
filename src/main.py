#!/usr/bin/env python3
"""USD1 Daily Report - Main entry point."""

import os
import sys
from datetime import date

import requests

from src.stablecoins import get_stablecoin_data
from src.adapters import ADAPTERS
from src.schema import Row


# Telegram config - Set these as environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Protocol URLs for linking
PROTOCOL_URLS = {
    "WLFI Markets": "https://markets.worldlibertyfinancial.com/market/0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d",
    "Echelon": "https://app.echelon.market/market/0xbb8f38636896c629ff9ef0bf916791a992e12ab4f1c6e26279ee9c6979646963?network=aptos_mainnet",
    "Kamino": "https://kamino.com/lend/steakhouse-usd1-high-yield",
    "Lista": "https://lista.org/lending/vault/bsc/0xfa27f172e0b6ebcef9c51abf817e2cb142fbe627?tab=vault",
    "JustLend": "https://app.justlend.org/marketDetailNew?jtokenAddress=TBEKggwqFkrc4KckQVR9BLucAmQugafEZf&_from=/homeNew&lang=en-US",
}

DEFILLAMA_URL = "https://defillama.com/stablecoins"
ASTER_URL = "https://coinmarketcap.com/exchanges/aster-pro/?type=spot"
ASTER_API_URL = "https://api.coinmarketcap.com/data-api/v3/exchange/market-pairs/latest?slug=aster-pro&category=spot&start=1&limit=100"


def fetch_usd1_markets() -> list[Row]:
    """Fetch USD1 lending market data from all adapters."""
    print("Fetching USD1 lending markets...")
    rows = []

    for protocol_name, fetch_func in ADAPTERS.items():
        try:
            row = fetch_func(timeout=20.0, debug=False)
            rows.append(row)
            print(f"  OK {protocol_name}")
        except Exception as e:
            print(f"  FAIL {protocol_name}: {e}")

    return rows


def fetch_aster_usd1_pairs() -> list[dict]:
    """Fetch USD1 trading pairs from Aster exchange via CoinMarketCap API."""
    print("Fetching Aster USD1 pairs...")
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(ASTER_API_URL, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    pairs = data["data"]["marketPairs"]

    usd1_pairs = []
    for p in pairs:
        if "USD1" in p["marketPair"]:
            usd1_pairs.append({
                "pair": p["marketPair"],
                "volume_usd": p["volumeUsd"],
            })

    usd1_pairs.sort(key=lambda x: x["volume_usd"], reverse=True)
    return usd1_pairs


def format_message(
    stablecoin_data: list[dict],
    usd1_data: list[Row],
    aster_data: list[dict],
) -> str:
    """Format data into Telegram message with clickable links."""
    today = date.today().isoformat()

    lines = [
        f"📊 DAILY REPORT | {today}",
        "",
        "USD1 MARKETS",
        "```",
        "          Supplied    Rate    Borrowed    Rate",
        "───────────────────────────────────────────────",
    ]

    # USD1 DeFi data - table part
    rate_details = []
    for row in usd1_data:
        protocol = row.protocol
        supplied = row.to_csv_dict()["total_supplied"]
        supply_rate = row.supply_rate
        borrowed = row.to_csv_dict()["total_borrowed"]
        borrow_rate = row.borrow_rate

        # Extract main rate (before parenthesis)
        supply_main = supply_rate.split("(")[0].strip() if "(" in supply_rate else supply_rate
        borrow_main = borrow_rate.split("(")[0].strip() if "(" in borrow_rate else borrow_rate

        short_name = protocol.replace(" Markets", "")
        lines.append(f"{short_name:<10} ${supplied:<9} {supply_main:<6}  ${borrowed:<9} {borrow_main}")

        # Collect rate details if they have breakdowns
        details = []
        if "(" in supply_rate:
            details.append("S: " + supply_rate.split("(")[1].rstrip(")"))
        if "(" in borrow_rate:
            details.append("B: " + borrow_rate.split("(")[1].rstrip(")"))
        if details:
            rate_details.append((short_name, " | ".join(details)))

    lines.append("```")

    # Rate details section
    if rate_details:
        lines.append("")
        lines.append("Rate details:")
        for name, detail in rate_details:
            lines.append(f"• {name}: {detail}")

    # Links section
    lines.append("")
    links = []
    for protocol, url in PROTOCOL_URLS.items():
        short_name = protocol.replace(" Markets", "")
        links.append(f"[{short_name}]({url})")
    lines.append("→ " + " | ".join(links))

    # Stablecoins section
    lines.append("")
    lines.append("STABLECOINS")
    lines.append("```")
    lines.append("Token  Market Cap    1D       7D")
    lines.append("─────────────────────────────────")

    for row in stablecoin_data:
        token = row["Token"]
        market_cap = row["Market Cap"]
        change_1d = row["1D Change"]
        change_7d = row["7D Change"]

        if change_1d and not change_1d.startswith("-"):
            change_1d = f"+{change_1d}"
        if change_7d and not change_7d.startswith("-"):
            change_7d = f"+{change_7d}"

        lines.append(f"{token:<5}  {market_cap:<11}  {change_1d:>7}  {change_7d:>7}")

    lines.append("```")
    lines.append(f"→ [DefiLlama]({DEFILLAMA_URL})")

    # Aster exchange section
    if aster_data:
        lines.append("")
        lines.append("ASTER USD1 PAIRS")
        lines.append("```")
        lines.append("Pair          Volume (24h)")
        lines.append("───────────────────────────")
        for p in aster_data:
            pair = p["pair"]
            vol = p["volume_usd"]
            if vol >= 1_000_000:
                vol_str = f"${vol/1_000_000:.2f}M"
            elif vol >= 1_000:
                vol_str = f"${vol/1_000:.0f}K"
            else:
                vol_str = f"${vol:.0f}"
            lines.append(f"{pair:<12}  {vol_str:>12}")
        lines.append("```")
        lines.append(f"→ [Aster]({ASTER_URL})")

    return "\n".join(lines)


def send_telegram_message(message: str) -> bool:
    """Send message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print("Message sent to Telegram successfully!")
        return True
    else:
        print(f"Failed to send message: {response.status_code}")
        print(response.text)
        return False


def main() -> int:
    """Main entry point."""
    # Check for required environment variables
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables are required.")
        print("Set them with:")
        print("  export TELEGRAM_BOT_TOKEN='your_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        return 1

    try:
        # Fetch all data
        print("Fetching stablecoin data...")
        stablecoin_data = get_stablecoin_data()

        usd1_data = fetch_usd1_markets()
        aster_data = fetch_aster_usd1_pairs()

        # Format message
        message = format_message(stablecoin_data, usd1_data, aster_data)

        print("\n" + "=" * 40)
        print("FORMATTED MESSAGE:")
        print("=" * 40)
        print(message)
        print("=" * 40 + "\n")

        # Send to Telegram
        if send_telegram_message(message):
            return 0
        else:
            return 1

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
