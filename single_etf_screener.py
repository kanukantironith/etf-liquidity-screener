"""
The Illiquidity Illusion: Single ETF Liquidity Screener
========================================================

Pulls an ETF's real holdings from SEC N-PORT filings, fetches trading data
for each underlying stock, and computes a Liquidity Mismatch Score out of 100.

Usage:
    python single_etf_screener.py

"""

import time
import numpy as np
import pandas as pd
from edgar import set_identity, Company
import yfinance as yf
from bidask import edge

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
ETF_TICKER = "ARKK"
CONTACT_EMAIL = "your.email@example.com"   # SEC requires a contact email
MAX_HOLDINGS = 63                          # cap on holdings to analyse
VOLUME_PARTICIPATION = 0.20                # max share of daily volume assumed safe

# Composite score weights (must sum to 1.0)
W_DTL, W_AMIHUD, W_SPREAD = 0.50, 0.30, 0.20


def scalar(x):
    """Safely pull a single float from a value or a one-element Series."""
    try:
        return float(x.iloc[0])
    except (AttributeError, IndexError):
        return float(x)


def rescale(col):
    """Scale a column to 0-1. Returns zeros if all values are equal."""
    lo, hi = col.min(), col.max()
    return col * 0 if hi == lo else (col - lo) / (hi - lo)


def get_holdings(ticker):
    """Fetch the latest N-PORT holdings for an ETF as a DataFrame."""
    set_identity(CONTACT_EMAIL)
    filing = Company(ticker).get_filings(form="NPORT-P").latest()
    nport = filing.obj()
    holdings = nport.investment_data()
    print(f"Holdings loaded: {len(holdings)} positions")
    return holdings


def fetch_prices(tickers):
    """Fetch 3 months of daily price/volume for each ticker. Skips failures."""
    price_data, failed = {}, []
    for t in tickers:
        try:
            df = yf.download(t, period="3mo", interval="1d",
                             progress=False, auto_adjust=True)
            if not df.empty and len(df) >= 20:
                price_data[t] = df
            else:
                failed.append(t)
        except Exception:
            failed.append(t)
        time.sleep(0.4)
    print(f"Priced {len(price_data)} of {len(tickers)} holdings "
          f"({len(failed)} could not be priced)")
    return price_data, failed


def compute_metrics(price_data):
    """Compute ADV, dollar volume, Amihud, and estimated spread per holding."""
    results = []
    for t, df in price_data.items():
        df = df.copy()
        adv = df['Volume'].tail(30).mean()
        avg_price = df['Close'].tail(30).mean()
        dollar_adv = scalar(adv) * scalar(avg_price)

        df['ret'] = df['Close'].pct_change().abs()
        df['dollar_vol'] = df['Close'] * df['Volume']
        amihud = (df['ret'] / df['dollar_vol']).tail(30).mean() * 1e6

        try:
            spread = edge(df['Open'], df['High'], df['Low'], df['Close'])
        except Exception:
            spread = np.nan

        results.append({
            'ticker': t,
            'adv_shares': round(scalar(adv)),
            'dollar_adv': round(dollar_adv),
            'amihud': scalar(amihud),
            'est_spread': spread,
        })
    return pd.DataFrame(results)


def build_score(metrics, holdings):
    """Join share counts, compute Days to Liquidate, and the Mismatch Score."""
    shares = holdings[['ticker', 'balance', 'value_usd', 'pct_value']].copy()
    for col in ['balance', 'value_usd', 'pct_value']:
        shares[col] = pd.to_numeric(shares[col], errors='coerce')

    m = metrics.merge(shares, on='ticker', how='left')
    m['dtl'] = m['balance'] / (VOLUME_PARTICIPATION * m['adv_shares'])

    # Clean broken rows (infinities, missing metrics, zero-volume placeholders)
    m = m.replace([np.inf, -np.inf], np.nan)
    m = m.dropna(subset=['dtl', 'amihud', 'est_spread'])
    m = m[m['adv_shares'] > 0]

    # Collapse duplicate tickers (same holding across share classes / lots)
    m = m.groupby('ticker', as_index=False).agg({
        'pct_value': 'sum', 'dtl': 'max',
        'amihud': 'max', 'est_spread': 'max',
    })

    m['dtl_s'] = rescale(m['dtl'])
    m['amihud_s'] = rescale(m['amihud'])
    m['spread_s'] = rescale(m['est_spread'])
    m['holding_risk'] = (W_DTL * m['dtl_s'] + W_AMIHUD * m['amihud_s']
                         + W_SPREAD * m['spread_s'])

    weight = m['pct_value'] / m['pct_value'].sum()
    lms = (m['holding_risk'] * weight).sum() * 100
    return m, lms


def main():
    print(f"\n=== Analysing {ETF_TICKER} ===\n")
    holdings = get_holdings(ETF_TICKER)

    top = holdings.sort_values('value_usd', ascending=False).head(MAX_HOLDINGS)
    tickers = top['ticker'].dropna().tolist()

    price_data, failed = fetch_prices(tickers)
    metrics = compute_metrics(price_data)
    scored, lms = build_score(metrics, holdings)

    ranking = scored.sort_values('holding_risk', ascending=False)
    print("\nRiskiest holdings (worst first):")
    print(ranking[['ticker', 'pct_value', 'dtl', 'amihud',
                   'est_spread', 'holding_risk']].head(10).round(3).to_string(index=False))

    print("\n" + "=" * 42)
    print(f"  {ETF_TICKER} LIQUIDITY MISMATCH SCORE: {lms:.1f} / 100")
    print("=" * 42)
    print(f"\nBased on {len(scored)} priceable holdings of {len(holdings)} total.")
    print("Note: unpriceable holdings tend to be the most illiquid,")
    print("so this score is a floor on the true risk.\n")

    # Save outputs
    import os
    os.makedirs("data", exist_ok=True)
    scored.to_csv(f"data/{ETF_TICKER}_analysis.csv", index=False)
    print(f"Saved data/{ETF_TICKER}_analysis.csv")


if __name__ == "__main__":
    main()
