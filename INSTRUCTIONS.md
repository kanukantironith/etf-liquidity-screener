# Setup and Run Instructions

There are two ways to run this project. If you have never used Python before, use Option A. If you are comfortable with a terminal, Option B runs it locally.

---

## Option A: Google Colab (no installation)

This runs in your browser on Google's machines. Nothing installs on your computer.

1. Go to [https://colab.research.google.com](https://colab.research.google.com) and sign in.
2. Click **File, then New notebook**.
3. Copy the contents of `single_etf_screener.py` into a cell.
4. At the very top of the cell, add this line to install the libraries:
   ```python
   !pip install edgartools yfinance bidask pandas pyarrow -q
   ```
5. Press **Shift and Enter** to run. The results print below the cell.

To run the market scan instead, do the same with `market_surface_scan.py`.

---

## Option B: Local machine (Mac, Windows, or Linux)

### Step 1: Check Python is installed

Open a terminal and run:

```bash
python3 --version
```

You need version 3.9 or higher. If it is missing, install it from [python.org/downloads](https://www.python.org/downloads/).

### Step 2: Download this project

Either download the ZIP from GitHub (green **Code** button, then **Download ZIP**) and unzip it, or clone it:

```bash
git clone https://github.com/YOUR_USERNAME/etf-liquidity-screener.git
cd etf-liquidity-screener
```

### Step 3: Create an isolated environment

This keeps the project's libraries separate from the rest of your system.

```bash
python3 -m venv venv
source venv/bin/activate        # on Windows use: venv\Scripts\activate
```

You should now see `(venv)` at the start of your terminal line.

### Step 4: Install the dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Run

Analyse a single ETF (default is ARKK):

```bash
python single_etf_screener.py
```

To analyse a different fund, open `single_etf_screener.py` and change the `ETF_TICKER` line near the top.

Run the market wide surface scan:

```bash
python market_surface_scan.py
```

To change how many ETFs are scanned, edit the `SCAN_LIMIT` line near the top of that file.

---

## What to Expect

- The single ETF screener takes about one to two minutes. Some holdings will fail to price (foreign or delisted tickers). This is expected and handled.
- The market scan takes roughly one minute per 100 ETFs, because it pauses politely between requests to avoid being rate limited by the data provider.
- Results print to the screen and are saved to the `data/` folder as CSV and Parquet files.

## Troubleshooting

- **A ticker column error:** the data library occasionally renames columns between versions. The scripts print available column names on startup so you can spot the correct one.
- **Empty or failed downloads:** thinly traded or delisted tickers often return no data from Yahoo Finance. The scripts skip these and continue.
- **Rate limiting on large scans:** if failures spike near the end of a big scan, the data provider is throttling. Wait a few minutes and re run, or reduce `SCAN_LIMIT`.
