# Amazon Buy Box Winner

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

Buy Box Checker is a tiny cross-platform tool that uses the **Rainforest API** to fetch Amazon **Buy Box** details. It prints a clean, vertical table for a single ASIN or processes a CSV and writes a tidy output file—no Amazon SP-API setup required.

## Features

* Single-ASIN mode (`--asin`) with a **clean, aligned** terminal table
* Batch mode: CSV in → CSV out (`--input-csv`, `--output-csv`)
* Fields captured:
  * **Title** (shortened for readability)
  * **Price** & currency
  * **Buy Box Exists** (Yes/No)
  * **Seller** (name & ID — Buy Box winner; if no Buy Box, top listing)
  * **Prime** (Yes/No)
  * **Discounted** (Yes/No)
  * **RRP** (if shown)
* Parallel workers for faster CSV runs (`--workers`)
* Works on **Windows / macOS / Linux** using a Python virtual environment

## Quick Start

1. **Get the files into a single folder**

   **Git (recommended):**
   ```bash
   git clone https://github.com/your-org/buybox-checker.git buybox-checker
   ```
   **Or download ZIP:**
   - Download the repository ZIP
   - Extract everything into a folder, e.g. `C:\Users\you\buybox-checker` or `/Users/you/buybox-checker`

   Your folder should contain:
   - `requirements.txt`
   - `rf_buybox.py`
   - `asins.csv`
   - `.env.rainforest` (you create this)

2. **Open a terminal *in that folder***
   - **Windows (PowerShell):** Right-click the folder → “Open in Terminal”, or `cd C:\Users\you\buybox-checker`
   - **macOS/Linux (Terminal):** `cd /Users/you/buybox-checker`

3. **Add your Rainforest API key**
   Create a file named **`.env.rainforest`** in the folder and paste:
   ```
   RAINFOREST_API_KEY=YOUR_KEY_HERE
   ```

4. **Set up Python (one-time)**

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   **Windows (PowerShell)**
   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   > If activation is blocked on Windows:  
   > `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

5. **Run it**

   **A) Single ASIN (prints a neat table)**
   ```bash
   python rf_buybox.py --asin B013Y78YY4 --domain amazon.co.uk
   ```

   **B) CSV mode (reads `asins.csv`, writes `out.csv`)**
   ```bash
   python rf_buybox.py --input-csv asins.csv --output-csv out.csv --domain amazon.co.uk --workers 5
   ```

   **`asins.csv` format**
   ```csv
   asin
   B013Y78YY4
   B0C7QX5Y7M
   ```

That’s it! You’ll see a compact table for single checks, and a CSV with columns:
`asin, product_name, price, currency, buybox_exists, seller_name, seller_id, prime, discounted, rrp, rrp_currency, error`.

## Example Output (single ASIN)

```
--------------------------------------------------------------
ASIN            : B013Y78YY4
Title           : Logitech G920 Driving Force wheel and pedals…
Price           : 169.39 GBP
Buy Box Exists  : Yes
Seller          : Amazon (ID: -)
Prime           : Yes
Discounted      : -
RRP             : -
--------------------------------------------------------------
```

## Tips & Troubleshooting

* `--domain` defaults to `amazon.co.uk`. Use `amazon.com`, `amazon.de`, etc. as needed.
* **Missing RAINFOREST_API_KEY** → ensure `.env.rainforest` exists in the same folder you’re running from.
* **429 / Too Many Requests** → lower concurrency: try `--workers 2` or run again later.
* Titles are auto-shortened for readability in terminal and CSV.
