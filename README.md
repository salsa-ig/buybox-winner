# Buy Box Checker (Rainforest API)

Checks Amazon **Buy Box** details for one ASIN or a CSV list.

## Files needed
- `requirements.txt`  
- `rf_buybox.py`  
- `asins.csv`  
- `.env.rainforest` (you create this with your API key)

---

## 1) Add your API key
Create a file named **`.env.rainforest`** in the same folder and paste:

```
RAINFOREST_API_KEY=YOUR_KEY_HERE
```

---

## 2) Open a terminal in this folder
- **Windows:** PowerShell → `cd C:\path\to\folder`
- **macOS/Linux:** Terminal → `cd /path/to/folder`

---

## 3) Set up Python (one-time)

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

## 4) Run it

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

**Tip:** `--domain` defaults to `amazon.co.uk`. Use `amazon.com`, `amazon.de`, etc., as needed. If you see “Missing RAINFOREST_API_KEY”, ensure `.env.rainforest` is in the same folder.
