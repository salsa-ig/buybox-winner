# Buy Box Checker (Rainforest API)

Checks Amazon **Buy Box** details for one ASIN or a CSV list.

---

## 1) Get the files into a single folder
**Option A — Git (recommended):**
```bash
git clone https://example.com/your-repo.git buybox-tool
```
**Option B — Download ZIP:**
- Download the project as a ZIP
- Extract all files into a folder, e.g. `C:\Users\you\buybox` or `/Users/you/buybox`

> Your folder should contain: `requirements.txt`, `rf_buybox.py`, `asins.csv` (example provided), and `.env.rainforest` (you create this).

---

## 2) Open a terminal **in that folder**
- **Windows (PowerShell):** Right‑click the folder → “Open in Terminal”, or `cd C:\Users\you\buybox`
- **macOS/Linux (Terminal):** `cd /Users/you/buybox` (or your path)

> Staying in this folder avoids “file not found” and missing‑key errors.

---

## 3) Add your Rainforest API key
Create a file named **`.env.rainforest`** in the folder and paste:
```
RAINFOREST_API_KEY=YOUR_KEY_HERE
```

---

## 4) Set up Python (one‑time)
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```powershell
# Windows (PowerShell)
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
> If activation is blocked on Windows, run:  
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

---

## 5) Run it

### A) Single ASIN (prints a neat table)
```bash
python rf_buybox.py --asin B013Y78YY4 --domain amazon.co.uk
```

### B) CSV mode (reads `asins.csv`, writes `out.csv`)
Your **`asins.csv`** should look like:
```csv
asin
B013Y78YY4
B0C7QX5Y7M
```
Run:
```bash
python rf_buybox.py --input-csv asins.csv --output-csv out.csv --domain amazon.co.uk --workers 5
```

---

## Output fields
- **Title** (shortened), **Price**, **Buy Box Exists (Yes/No)**, **Seller (name & ID)**, **Prime (Yes/No)**, **Discounted (Yes/No)**, **RRP**.  
- If no Buy Box exists, the script shows the **top listing seller** instead.

**Tip:** `--domain` defaults to `amazon.co.uk`. Use `amazon.com`, `amazon.de`, etc. If you see “Missing RAINFOREST_API_KEY”, make sure `.env.rainforest` is in this folder.
