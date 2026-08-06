"""
The Illiquidity Illusion: Market-Wide Surface Liquidity Scan
============================================================

Screens hundreds of ETFs on their own trading characteristics (dollar volume,
Amihud illiquidity, estimated spread) and ranks the market from most to least
surface-fragile.

This measures SURFACE liquidity: how easily each ETF itself trades. It is the
deliberate contrast to the look-through screener, which sees inside the fund.
An ETF can look liquid here yet be fragile underneath.

Usage:
    python market_surface_scan.py
"""

import time
import numpy as np
import pandas as pd
import yfinance as yf
from bidask import edge

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
SCAN_LIMIT = 700          # how many ETFs to scan
MIN_HISTORY = 20          # minimum trading days required

# Surface risk weights (must sum to 1.0)
W_VOL, W_AMIHUD, W_SPREAD = 0.40, 0.35, 0.25

NASDAQ_LISTED = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"


def scalar(x):
    try:
        return float(x.iloc[0])
    except (AttributeError, IndexError):
        return float(x)


def rescale(col):
    lo, hi = col.min(), col.max()
    return col * 0 if hi == lo else (col - lo) / (hi - lo)


def get_etf_list():
    """Pull the public NASDAQ symbol directory and filter to ETFs."""
    frames = [pd.read_csv(NASDAQ_LISTED, sep="|"),
              pd.read_csv(OTHER_LISTED, sep="|")]
    raw = pd.concat(frames, ignore_index=True)

    raw['ticker'] = raw['Symbol'].fillna(raw['ACT Symbol'])
    etfs = raw[(raw['ETF'] == 'Y') & (raw['Test Issue'] != 'Y')].copy()
    etfs = etfs.dropna(subset=['ticker'])
    etfs = etfs[~etfs['ticker'].str.contains(r'[\$\.]', na=False)]
    etfs = etfs.drop_duplicates(subset=['ticker'])

    tickers = etfs['ticker'].tolist()
    print(f"Total ETFs found: {len(tickers)}")
    return tickers


def scan(tickers):
    """Compute surface liquidity metrics for each ETF."""
    rows, failed = [], []
    total = len(tickers)
    for i, t in enumerate(tickers, 1):
        try:
            df = yf.download(t, period="3mo", interval="1d",
                             progress=False, auto_adjust=True)
            if df.empty or len(df) < MIN_HISTORY:
                failed.append(t)
            else:
                adv = df['Volume'].tail(30).mean()
                price = df['Close'].tail(30).mean()
                dollar_adv = scalar(adv) * scalar(price)

                df = df.copy()
                df['ret'] = df['Close'].pct_change().abs()
                df['dvol'] = df['Close'] * df['Volume']
                amihud = (df['ret'] / df['dvol']).tail(30).mean() * 1e6

                try:
                    spread = edge(df['Open'], df['High'], df['Low'], df['Close'])
                except Exception:
                    spread = np.nan

                rows.append({'ticker': t, 'dollar_adv': round(dollar_adv),
                             'amihud': scalar(amihud), 'est_spread': spread})
        except Exception:
            failed.append(t)

        if i % 25 == 0:
            print(f"  {i}/{total} done ({len(rows)} ok, {len(failed)} failed)")
        time.sleep(0.4)

    print(f"\nScanned {total} ETFs -> {len(rows)} usable, {len(failed)} failed")
    return pd.DataFrame(rows)


def rank(surface):
    """Blend surface metrics into a 0-100 risk score and sort worst-first."""
    r = surface.replace([np.inf, -np.inf], np.nan)
    r = r.dropna(subset=['dollar_adv', 'amihud', 'est_spread'])
    r = r[r['dollar_adv'] > 0]

    # Low dollar volume means risky, so invert it
    r['illiq_vol'] = 1 - rescale(r['dollar_adv'])
    r['illiq_amihud'] = rescale(r['amihud'])
    r['illiq_spread'] = rescale(r['est_spread'])
    r['surface_risk'] = (W_VOL * r['illiq_vol']
                         + W_AMIHUD * r['illiq_amihud']
                         + W_SPREAD * r['illiq_spread']) * 100
    return r.sort_values('surface_risk', ascending=False)


def main():
    print("\n=== Market-Wide ETF Surface Liquidity Scan ===\n")
    tickers = get_etf_list()[:SCAN_LIMIT]
    print(f"Scanning first {len(tickers)}...\n")

    surface = scan(tickers)
    ranked = rank(surface)

    print("\n=== 15 MOST SURFACE-FRAGILE ETFs ===")
    print(ranked[['ticker', 'dollar_adv', 'amihud', 'est_spread',
                  'surface_risk']].head(15).round(2).to_string(index=False))

    print("\n=== 10 MOST LIQUID ETFs ===")
    print(ranked[['ticker', 'dollar_adv',
                  'surface_risk']].tail(10).round(2).to_string(index=False))

    import os
    os.makedirs("data", exist_ok=True)
    ranked.to_csv("data/etf_surface_scan.csv", index=False)
    print("\nSaved data/etf_surface_scan.csv")


if __name__ == "__main__":
    main()
