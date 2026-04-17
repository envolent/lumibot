# Stock Analytics Report — April 2026

This directory contains generated outputs from `stock_report.py`.

## Contents

| File | Description |
|------|-------------|
| `stock_analytics_report_april2026.pdf` | Full 8-page PDF report |
| `NVDA_chart.png` | NVIDIA price + MA + RSI + volume chart |
| `LRCX_chart.png` | Lam Research chart |
| `NBIS_chart.png` | Nebius Group chart |
| `META_chart.png` | Meta Platforms chart |
| `AVGO_chart.png` | Broadcom chart |
| `comparison_chart.png` | Upside bar chart + 6-month normalized performance |
| `analyst_summary.png` | Ratings pie, analyst coverage bar, valuation scatter |

## Regenerate the Report

```bash
# Install dependencies (one-time)
pip install matplotlib reportlab numpy requests pytz beautifulsoup4 frozendict

# Run from repo root
python3 stock_report.py
```

Outputs are written to `stock_reports/`.

## Stocks Covered

| Ticker | Company | Projected Upside | Rating |
|--------|---------|-----------------|--------|
| NVDA | NVIDIA Corporation | +32.4% | Strong Buy |
| LRCX | Lam Research | +26.3% | Strong Buy |
| NBIS | Nebius Group | +110.0% | Buy |
| META | Meta Platforms | +18.5% | Strong Buy |
| AVGO | Broadcom Inc. | +10.3% | Strong Buy |

> Data sourced from Yahoo Finance (live prices) and Wall Street analyst consensus
> (MarketBeat, TipRanks, 24/7 Wall St.). Not financial advice.
