"""
Stock Analytics Report Generator
Fetches real price data from Yahoo Finance and generates charts + PDF
for 5 stocks with 10%+ projected upside (April 2026)
"""

import requests
import json
import datetime
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

OUTPUT_DIR = "/home/user/lumibot/stock_reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

STOCKS = {
    "NVDA": {
        "name": "NVIDIA Corporation",
        "sector": "Semiconductors",
        "current_target": 264.54,
        "upside_pct": 32.37,
        "rating": "Strong Buy",
        "analysts": 63,
        "forward_pe": 23.9,
        "reason": "AI infrastructure dominance; revenue growth accelerating through 2026. "
                  "Hyperscaler capex continues funneling into NVDA hardware.",
        "color": "#76b900",
    },
    "LRCX": {
        "name": "Lam Research Corporation",
        "sector": "Semiconductor Equipment",
        "current_target": 275.10,
        "upside_pct": 26.30,
        "rating": "Strong Buy",
        "analysts": 31,
        "forward_pe": 19.4,
        "reason": "Semiconductor equipment leader with strong earnings growth. "
                  "Cantor Fitzgerald raised target to $320; Argus raised to $280.",
        "color": "#0077cc",
    },
    "NBIS": {
        "name": "Nebius Group",
        "sector": "AI Cloud Infrastructure",
        "current_target": None,
        "upside_pct": 110.0,
        "rating": "Buy",
        "analysts": 8,
        "forward_pe": None,
        "reason": "Fast-growing AI neocloud provider. Up 73% YTD 2026. "
                  "Revenue path to $9.7B could push market cap to ~$78B.",
        "color": "#e63946",
    },
    "META": {
        "name": "Meta Platforms Inc.",
        "sector": "Social Media / AI",
        "current_target": 660.0,
        "upside_pct": 18.5,
        "rating": "Strong Buy",
        "analysts": 58,
        "forward_pe": 22.0,
        "reason": "Cheapest Mag-7 stock at 22x forward earnings. Strong AI ad "
                  "targeting and AR hardware pipeline (Ray-Ban, Orion).",
        "color": "#1877f2",
    },
    "AVGO": {
        "name": "Broadcom Inc.",
        "sector": "Semiconductors",
        "current_target": 438.43,
        "upside_pct": 10.25,
        "rating": "Strong Buy",
        "analysts": 28,
        "forward_pe": 26.1,
        "reason": "Custom AI chip demand surging from Google & Meta. "
                  "BofA top-6 large-cap chip pick; largest upside among peers.",
        "color": "#cc0000",
    },
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockReportBot/1.0)"}


def fetch_price_history(ticker, range_="6mo", interval="1d"):
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?interval={interval}&range={range_}"
    )
    resp = requests.get(url, headers=HEADERS, timeout=15)
    data = resp.json()
    result = data.get("chart", {}).get("result")
    if not result:
        return None, None, None
    r = result[0]
    timestamps = r["timestamp"]
    closes = r["indicators"]["quote"][0]["close"]
    volumes = r["indicators"]["quote"][0].get("volume", [])
    dates = [datetime.datetime.utcfromtimestamp(t).date() for t in timestamps]
    # Clean None values
    clean = [(d, c, v) for d, c, v in zip(dates, closes, volumes) if c is not None]
    dates, closes, volumes = zip(*clean) if clean else ([], [], [])
    return list(dates), list(closes), list(volumes)


def compute_moving_averages(closes, windows=(20, 50)):
    closes = np.array(closes, dtype=float)
    result = {}
    for w in windows:
        ma = np.full_like(closes, np.nan)
        for i in range(w - 1, len(closes)):
            ma[i] = closes[i - w + 1 : i + 1].mean()
        result[w] = ma
    return result


def compute_rsi(closes, period=14):
    closes = np.array(closes, dtype=float)
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    rsi = np.full(len(closes), np.nan)
    if len(gains) < period:
        return rsi
    avg_gain = gains[:period].mean()
    avg_loss = losses[:period].mean()
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 100
        rsi[i + 1] = 100 - 100 / (1 + rs)
    return rsi


def plot_stock(ticker, info, dates, closes, volumes, pdf):
    mas = compute_moving_averages(closes)
    rsi = compute_rsi(closes)
    color = info["color"]

    fig = plt.figure(figsize=(14, 10))
    fig.patch.set_facecolor("#0d1117")
    gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1], hspace=0.08)

    # ── Price + MA chart ────────────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor("#0d1117")
    ax1.plot(dates, closes, color=color, linewidth=1.8, label="Close", zorder=3)
    ax1.fill_between(dates, closes, min(closes), alpha=0.12, color=color)
    ax1.plot(dates, mas[20], color="#f0c040", linewidth=1.2, linestyle="--", label="MA 20", zorder=2)
    ax1.plot(dates, mas[50], color="#c0c0ff", linewidth=1.2, linestyle="--", label="MA 50", zorder=2)

    # Analyst target line
    if info["current_target"]:
        ax1.axhline(info["current_target"], color="#00ff99", linewidth=1.2,
                    linestyle=":", label=f"Analyst Target ${info['current_target']:.2f}")

    ax1.set_xlim(dates[0], dates[-1])
    ax1.set_ylabel("Price (USD)", color="white", fontsize=10)
    ax1.tick_params(colors="white", labelsize=8)
    for spine in ax1.spines.values():
        spine.set_edgecolor("#333")
    ax1.legend(loc="upper left", fontsize=8, facecolor="#1a1a2e", labelcolor="white",
               framealpha=0.8)
    ax1.grid(axis="y", color="#222", linewidth=0.5)

    pct_chg = (closes[-1] - closes[0]) / closes[0] * 100
    ax1.set_title(
        f"{ticker}  —  {info['name']}\n"
        f"Current: ${closes[-1]:.2f}   6-mo Chg: {pct_chg:+.1f}%   "
        f"Analyst Target: {'+' if info['upside_pct']>0 else ''}{info['upside_pct']:.1f}% upside   "
        f"Rating: {info['rating']}",
        color="white", fontsize=11, fontweight="bold", pad=10,
    )

    # ── Volume ──────────────────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.set_facecolor("#0d1117")
    bar_colors = [color if c >= o else "#555" for c, o in zip(closes[1:], closes[:-1])]
    ax2.bar(dates[1:], volumes[1:], color=bar_colors, width=1.0, alpha=0.7)
    ax2.set_ylabel("Volume", color="white", fontsize=9)
    ax2.tick_params(colors="white", labelsize=7)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))
    for spine in ax2.spines.values():
        spine.set_edgecolor("#333")
    ax2.grid(axis="y", color="#222", linewidth=0.4)
    plt.setp(ax2.get_xticklabels(), visible=False)

    # ── RSI ─────────────────────────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.set_facecolor("#0d1117")
    ax3.plot(dates, rsi, color="#ff9f1c", linewidth=1.3, label="RSI(14)")
    ax3.axhline(70, color="#ff4444", linewidth=0.8, linestyle="--")
    ax3.axhline(30, color="#44ff88", linewidth=0.8, linestyle="--")
    ax3.fill_between(dates, rsi, 70, where=(np.array(rsi) >= 70), alpha=0.2, color="#ff4444")
    ax3.fill_between(dates, rsi, 30, where=(np.array(rsi) <= 30), alpha=0.2, color="#44ff88")
    ax3.set_ylim(0, 100)
    ax3.set_ylabel("RSI", color="white", fontsize=9)
    ax3.tick_params(colors="white", labelsize=7)
    for spine in ax3.spines.values():
        spine.set_edgecolor("#333")
    ax3.grid(axis="y", color="#222", linewidth=0.4)
    ax3.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b '%y"))
    fig.autofmt_xdate(rotation=30, ha="right")

    # Save individual PNG
    png_path = os.path.join(OUTPUT_DIR, f"{ticker}_chart.png")
    plt.savefig(png_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    pdf.savefig(fig, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  ✓ {ticker} chart saved")
    return png_path


def plot_comparison_page(all_data, pdf):
    """Bar chart: Projected upside % for all 5 stocks."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#0d1117")

    tickers = list(STOCKS.keys())
    upsides = [STOCKS[t]["upside_pct"] for t in tickers]
    colors = [STOCKS[t]["color"] for t in tickers]
    names = [STOCKS[t]["name"].split()[0] + "\n" + tickers[i] for i, t in enumerate(tickers)]

    # Left: upside bar chart
    ax = axes[0]
    ax.set_facecolor("#0d1117")
    bars = ax.barh(names, upsides, color=colors, edgecolor="#333", height=0.55)
    ax.axvline(10, color="white", linewidth=1, linestyle="--", alpha=0.5, label="10% threshold")
    for bar, val in zip(bars, upsides):
        ax.text(val + 1, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", color="white", fontsize=9, fontweight="bold")
    ax.set_xlabel("Projected Upside (%)", color="white")
    ax.set_title("Analyst Consensus Upside Targets", color="white", fontweight="bold")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    ax.grid(axis="x", color="#222", linewidth=0.5)
    ax.legend(fontsize=8, facecolor="#1a1a2e", labelcolor="white")

    # Right: 6-month normalised performance (all start at 100)
    ax2 = axes[1]
    ax2.set_facecolor("#0d1117")
    for ticker, (dates, closes, _) in all_data.items():
        if closes:
            norm = [c / closes[0] * 100 for c in closes]
            ax2.plot(dates, norm, color=STOCKS[ticker]["color"],
                     linewidth=1.8, label=ticker)
    ax2.axhline(100, color="#555", linewidth=0.8, linestyle="--")
    ax2.set_ylabel("Normalized Price (Base=100)", color="white")
    ax2.set_title("6-Month Relative Performance", color="white", fontweight="bold")
    ax2.legend(fontsize=9, facecolor="#1a1a2e", labelcolor="white")
    ax2.tick_params(colors="white")
    for spine in ax2.spines.values():
        spine.set_edgecolor("#333")
    ax2.grid(color="#222", linewidth=0.4)
    ax2.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b '%y"))
    fig.autofmt_xdate(rotation=30, ha="right")

    fig.suptitle("Portfolio Overview — 5 Stocks With 10%+ Upside (April 2026)",
                 color="white", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    png_path = os.path.join(OUTPUT_DIR, "comparison_chart.png")
    plt.savefig(png_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    pdf.savefig(fig, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  ✓ Comparison chart saved")


def plot_cover_page(pdf):
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")
    ax.axis("off")

    ax.text(0.5, 0.88, "STOCK ANALYTICS REPORT", ha="center", va="center",
            fontsize=28, fontweight="bold", color="white", transform=ax.transAxes)
    ax.text(0.5, 0.80, "5 Stocks Projected for 10%+ Upside", ha="center", va="center",
            fontsize=18, color="#aaaaaa", transform=ax.transAxes)
    ax.text(0.5, 0.74, f"Generated: {datetime.date.today().strftime('%B %d, %Y')}",
            ha="center", va="center", fontsize=13, color="#666", transform=ax.transAxes)

    # Table
    col_labels = ["Ticker", "Company", "Sector", "Rating", "Upside", "Analysts", "Fwd P/E"]
    rows = []
    for t, info in STOCKS.items():
        pe = f"{info['forward_pe']}x" if info["forward_pe"] else "N/A"
        rows.append([t, info["name"], info["sector"], info["rating"],
                     f"+{info['upside_pct']:.1f}%", str(info["analysts"]), pe])

    table = ax.table(
        cellText=rows, colLabels=col_labels,
        loc="center", cellLoc="center",
        bbox=[0.02, 0.30, 0.96, 0.38],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (r, c), cell in table.get_celld().items():
        cell.set_facecolor("#1a1a2e" if r > 0 else "#222244")
        cell.set_text_props(color="white")
        cell.set_edgecolor("#333")
        if r > 0 and c == 4:  # Upside column
            cell.set_text_props(color="#00ff99", fontweight="bold")
        if r > 0 and c == 3:  # Rating
            cell.set_text_props(color="#f0c040")

    ax.text(0.5, 0.17,
            "Data sourced from Yahoo Finance & Wall Street analyst consensus (MarketBeat, TipRanks, 24/7 Wall St.)\n"
            "This report is for informational purposes only and does not constitute financial advice.\n"
            "Analyst targets are 12-month projections. All investments carry risk.",
            ha="center", va="center", fontsize=9, color="#666",
            transform=ax.transAxes, style="italic")

    pdf.savefig(fig, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  ✓ Cover page created")


def plot_analyst_detail_page(pdf):
    """Summary page with analyst details per stock."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 7))
    fig.patch.set_facecolor("#0d1117")

    # ── Pie: Rating distribution ─────────────────────────────────────────
    ax = axes[0]
    ax.set_facecolor("#0d1117")
    ratings = {"Strong Buy": 4, "Buy": 1}
    wedge_colors = ["#00cc66", "#44aaff"]
    wedges, texts, autotexts = ax.pie(
        ratings.values(), labels=ratings.keys(), colors=wedge_colors,
        autopct="%1.0f%%", startangle=90,
        textprops={"color": "white", "fontsize": 10},
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(10)
    ax.set_title("Consensus Ratings", color="white", fontweight="bold")

    # ── Bar: Number of analysts ──────────────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor("#0d1117")
    tickers = list(STOCKS.keys())
    analyst_counts = [STOCKS[t]["analysts"] for t in tickers]
    colors = [STOCKS[t]["color"] for t in tickers]
    bars = ax2.bar(tickers, analyst_counts, color=colors, edgecolor="#333", width=0.5)
    for bar, val in zip(bars, analyst_counts):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 str(val), ha="center", color="white", fontsize=9, fontweight="bold")
    ax2.set_ylabel("# of Analysts", color="white")
    ax2.set_title("Analyst Coverage", color="white", fontweight="bold")
    ax2.tick_params(colors="white")
    for spine in ax2.spines.values():
        spine.set_edgecolor("#333")
    ax2.set_facecolor("#0d1117")
    ax2.grid(axis="y", color="#222", linewidth=0.5)

    # ── Scatter: Forward P/E vs Upside ───────────────────────────────────
    ax3 = axes[2]
    ax3.set_facecolor("#0d1117")
    for t, info in STOCKS.items():
        if info["forward_pe"]:
            ax3.scatter(info["forward_pe"], info["upside_pct"],
                        color=info["color"], s=180, zorder=3, edgecolors="white", linewidths=0.8)
            ax3.annotate(t, (info["forward_pe"], info["upside_pct"]),
                         textcoords="offset points", xytext=(6, 4),
                         color="white", fontsize=9)
    ax3.set_xlabel("Forward P/E", color="white")
    ax3.set_ylabel("Projected Upside (%)", color="white")
    ax3.set_title("Valuation vs. Upside", color="white", fontweight="bold")
    ax3.tick_params(colors="white")
    for spine in ax3.spines.values():
        spine.set_edgecolor("#333")
    ax3.grid(color="#222", linewidth=0.4)

    fig.suptitle("Analyst Metrics Summary", color="white", fontsize=14,
                 fontweight="bold", y=1.02)
    plt.tight_layout()
    png_path = os.path.join(OUTPUT_DIR, "analyst_summary.png")
    plt.savefig(png_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    pdf.savefig(fig, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print("  ✓ Analyst summary page saved")


def main():
    pdf_path = os.path.join(OUTPUT_DIR, "stock_analytics_report_april2026.pdf")
    all_data = {}

    print("Fetching price data...")
    for ticker in STOCKS:
        dates, closes, volumes = fetch_price_history(ticker)
        all_data[ticker] = (dates, closes, volumes)
        last = closes[-1] if closes else "N/A"
        print(f"  {ticker}: {len(closes)} data points, last close ${last:.2f}" if closes else f"  {ticker}: no data")

    print("\nBuilding PDF report...")
    with PdfPages(pdf_path) as pdf:
        plot_cover_page(pdf)
        plot_comparison_page(all_data, pdf)
        plot_analyst_detail_page(pdf)
        for ticker, info in STOCKS.items():
            dates, closes, volumes = all_data[ticker]
            if dates:
                plot_stock(ticker, info, dates, closes, volumes, pdf)

        # PDF metadata
        meta = pdf.infodict()
        meta["Title"] = "Stock Analytics Report — April 2026"
        meta["Author"] = "LumiBot Analytics"
        meta["Subject"] = "5 stocks projected for 10%+ upside"
        meta["CreationDate"] = datetime.datetime.now()

    print(f"\nReport saved to: {pdf_path}")
    print(f"Individual charts saved to: {OUTPUT_DIR}/")

    # List all outputs
    for f in sorted(os.listdir(OUTPUT_DIR)):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"  {f}  ({size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
