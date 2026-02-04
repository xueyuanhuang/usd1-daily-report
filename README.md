# USD1 Daily Report

Automated daily report for USD1 stablecoin metrics, DeFi lending rates, and exchange volumes. Sends formatted reports to Telegram.

## Features

- **Stablecoin Market Caps**: USDT, USDC, USD1, U from DefiLlama
- **USD1 Lending Markets**: WLFI, Echelon, Kamino, Lista, JustLend
- **Aster Exchange Volumes**: USD1 trading pairs from CoinMarketCap

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/usd1-daily-report.git
cd usd1-daily-report

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Edit `src/main.py` to set your Telegram credentials:

```python
TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
```

## Usage

```bash
# Run the report
python -m src.main
```

## Output Example

```
📊 DAILY REPORT | 2026-02-04

USD1 MARKETS
          Supplied    Rate    Borrowed    Rate
───────────────────────────────────────────────
WLFI       $139.45M   8.75%   $109.99M   5.14%
Echelon    $9.40M     7.60%   $6.80M     7.38%
...

STABLECOINS
Token  Market Cap    1D       7D
─────────────────────────────────
USDT   $185.458B     +0.21%   -0.38%
...

ASTER USD1 PAIRS
Pair          Volume (24h)
───────────────────────────
YI/USD1             $8.55M
...
```
