# The Illiquidity Illusion: An ETF Liquidity Risk Screener

> ETFs promise instant liquidity to investors, yet the assets inside them may trade rarely. This project quantifies that hidden mismatch, the gap between how easily an ETF trades and how easily its underlying holdings could actually be sold in a crisis.

## The Problem

An Exchange Traded Fund trades on the secondary market like a stock, but the assets it holds trade on their own primary markets. A dangerous gap opens up when a fund itself changes hands millions of times a day while the securities inside it barely move. In a market panic, Authorized Participants cannot unwind the underlying positions fast enough to match the ETF sell off, and the fund's price can break away from its Net Asset Value.

Standard liquidity checks look at how much the ETF itself trades. That number can be an illusion. This tool looks under the hood.

## What This Project Does

It works on two levels:

1. **Look through analysis (single ETF).** It pulls a fund's real holdings straight from SEC regulatory filings (Form N-PORT), fetches trading data for each underlying stock, and computes a per holding liquidity profile: Average Daily Volume, Days to Liquidate, the Amihud illiquidity ratio, and an estimated bid ask spread. These roll up into a single Liquidity Mismatch Score out of 100.

2. **Market wide surface scan.** It screens hundreds of ETFs on their own trading characteristics to rank the market from most to least fragile, providing the contrast that exposes where surface liquidity and true liquidity diverge.

## Key Metrics Explained

| Metric | What it measures | Why it matters |
|--------|------------------|----------------|
| Average Daily Volume (ADV) | Typical shares traded per day over 30 days | Baseline liquidity of a holding |
| Days to Liquidate (DTL) | Shares held / (20% of daily volume) | How many days to exit a position without crashing the price. The industry assumes a fund can safely be at most 20% of daily volume |
| Amihud Illiquidity | Average of daily absolute return / daily dollar volume | Price impact per dollar traded. Higher means more illiquid |
| Estimated Bid Ask Spread | Corwin Schultz / EDGE estimator from daily high low prices | Hidden transaction cost, without needing paid intraday data |
| Liquidity Mismatch Score | Fund weighted blend of the above, scaled 0 to 100 | The single boardroom ready risk headline |

## Example Result: ARKK

Running the look through on ARKK (63 holdings) produced a Mismatch Score with the risk heavily concentrated in a small cluster of holdings. The two riskiest positions carried Days to Liquidate figures of over three weeks each, while the bulk of the fund was highly liquid. The tool's value is not the single number but the fact that it names *which* holdings would break first.

A notable finding: roughly a third of ARKK's holdings could not be priced through standard data feeds at all, overwhelmingly thinly traded foreign listings. The holdings hardest to get data on are, almost by definition, the hardest to sell. The data gap is itself a liquidity signal, and the reported score is therefore a floor on the true risk, not the full picture.

## Data Sources

All sources are free and require no paid subscription.

- **ETF holdings:** [SEC EDGAR](https://www.sec.gov/), Form N-PORT, accessed via the [edgartools](https://pypi.org/project/edgartools/) library. This is the primary regulatory filing every US registered fund must submit.
- **Pricing and volume:** [yfinance](https://pypi.org/project/yfinance/), pulling from Yahoo Finance.
- **Spread estimation:** [bidask](https://github.com/eguidotti/bidask), implementing the peer reviewed Corwin Schultz and EDGE estimators.
- **ETF universe list:** [NASDAQ Trader symbol directory](https://www.nasdaqtrader.com/), public domain.

## How to Run

See [INSTRUCTIONS.md](INSTRUCTIONS.md) for full step by step setup, including a zero installation option using Google Colab.

Quick version:

```bash
pip install -r requirements.txt
python single_etf_screener.py    # analyse one ETF
python market_surface_scan.py    # scan the market
```

## Repository Contents

| File | Purpose |
|------|---------|
| `single_etf_screener.py` | Look through analysis for one ETF |
| `market_surface_scan.py` | Market wide surface liquidity scan |
| `INSTRUCTIONS.md` | Detailed setup and run guide |
| `requirements.txt` | Python dependencies |
| `data/` | Sample output files |

## Methodology Notes and Limitations

- N-PORT filings are quarterly with a reporting lag, so holdings are as of the last filing, not live.
- The Mismatch Score is computed only on priceable holdings; unpriceable ones tend to be the most illiquid, so the score understates true risk.
- The surface scan measures each ETF's own trading and cannot see through to holdings. It answers "which ETFs look hard to trade", while the look through answers the deeper "which are hard to trade for reasons the surface hides".
- Metric weights in the composite score are a deliberate choice (Days to Liquidate weighted most heavily) and can be adjusted.

## Author

Built as a demonstration of quantitative finance, data engineering, and market microstructure literacy.
