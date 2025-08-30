#!/usr/bin/env python3
import argparse, csv, os, sys, time
from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import requests

API_URL = "https://api.rainforestapi.com/request"

# Display defaults (no CLI flags, just clean output)
TITLE_MAX_TERM = 60   # terminal print
TITLE_MAX_CSV  = 80   # CSV output

# -------------------- helpers --------------------

def get_api_key() -> str:
    k = os.getenv("RAINFOREST_API_KEY")
    if not k:
        raise SystemExit("Missing RAINFOREST_API_KEY (set it in .env.rainforest or your environment).")
    return k.strip()

def to_float(x) -> Optional[float]:
    if x is None: return None
    try:
        return float(x)
    except Exception:
        return None

def shorten(text: Optional[str], max_len: int) -> Optional[str]:
    if not text:
        return text
    t = " ".join(str(text).split())  # collapse whitespace/newlines
    if len(t) <= max_len:
        return t
    cut = t[:max_len].rsplit(" ", 1)[0]
    return (cut if cut else t[:max_len]) + "…"

def rf_get(params: Dict[str, Any], retries: int = 3, timeout: int = 30) -> Dict[str, Any]:
    """GET with simple exponential backoff for 429/5xx."""
    backoff = 1.0
    for i in range(retries + 1):
        r = requests.get(API_URL, params=params, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504) and i < retries:
            time.sleep(backoff)
            backoff *= 2
            continue
        try:
            j = r.json()
        except Exception:
            j = {"error": r.text}
        raise RuntimeError(f"HTTP {r.status_code}: {j}")

def pick_buybox_from_offers(offers_json: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Returns: (buybox_exists, buybox_offer, top_offer)
    - buybox_offer: offer with buybox_winner==True (if any)
    - top_offer: first offer in list (useful when no buy box)
    """
    offers = offers_json.get("offers") or []
    bb = next((o for o in offers if o.get("buybox_winner") is True), None)
    top = offers[0] if offers else None
    return (bb is not None, bb, top)

def extract_money(m: Optional[Dict[str, Any]]) -> Tuple[Optional[float], Optional[str]]:
    if not isinstance(m, dict):
        return None, None
    return to_float(m.get("value")), m.get("currency")

# -------------------- core fetch/parse --------------------

def fetch_asin(api_key: str, asin: str, domain: str) -> Dict[str, Any]:
    """
    Fetch product + offers, prefer offers buy box for seller/price/prime,
    fall back to product fields as needed. Also report if buy box exists.
    """
    # 1) Product page (title + sometimes buybox/savings/list_price)
    prod = rf_get({"api_key": api_key, "type": "product", "amazon_domain": domain, "asin": asin})
    p = prod.get("product") or {}

    title = p.get("title")
    product_rrp_val, product_rrp_ccy = extract_money(p.get("list_price"))
    product_savings_val = to_float((p.get("savings") or {}).get("value"))
    bb_prod = p.get("buybox_winner") or {}

    # 2) Offers page — reliable for seller + prime + price + existence of buy box
    offers = rf_get({"api_key": api_key, "type": "offers", "amazon_domain": domain, "asin": asin})
    buybox_exists, bb_offer, top_offer = pick_buybox_from_offers(offers)

    # Choose the source offer (buybox if exists, else top offer)
    chosen = bb_offer if buybox_exists else top_offer

    # Price from chosen offer (fallback to product buybox if needed)
    price_val, price_ccy = extract_money((chosen.get("price") or {}) if chosen else {})
    if price_val is None:
        price_val, price_ccy = extract_money(bb_prod.get("price") or {})

    # Seller (buybox seller if exists; otherwise top listing seller)
    seller_obj = (chosen or {}).get("seller") or {}
    seller_name = seller_obj.get("name") or (bb_prod.get("seller") or {}).get("name")
    seller_id   = seller_obj.get("id")   or (bb_prod.get("seller") or {}).get("id")

    # Prime flag
    prime = (chosen or {}).get("is_prime")
    if prime is None:
        prime = bb_prod.get("is_prime")

    # Buy Box RRP if present on chosen offer; else product-level list_price
    chosen_rrp_val, chosen_rrp_ccy = extract_money((chosen.get("rrp") or {}) if chosen else {})
    rrp_val = chosen_rrp_val if chosen_rrp_val is not None else product_rrp_val
    rrp_ccy = chosen_rrp_ccy if chosen_rrp_ccy is not None else product_rrp_ccy

    # Discounted? Prefer comparing price < RRP; otherwise use savings-like fields
    discounted: Optional[bool] = None
    if rrp_val is not None and price_val is not None:
        discounted = (price_val < (rrp_val - 1e-9))
    else:
        candidates = [
            product_savings_val,
            to_float(((chosen or {}).get("save") or {}).get("value")),
            to_float(((chosen or {}).get("savings") or {}).get("value")),
            to_float(((chosen or {}).get("amazon_discount") or {}).get("value")),
            to_float((bb_prod.get("save") or {}).get("value")),
            to_float((bb_prod.get("savings") or {}).get("value")),
            to_float((bb_prod.get("amazon_discount") or {}).get("value")),
        ]
        for v in candidates:
            if v is not None:
                discounted = v > 0
                break

    return dict(
        product_name=title,
        price=price_val,
        currency=price_ccy,
        buybox_exists=buybox_exists,
        seller_name=seller_name,
        seller_id=seller_id,
        prime=prime,
        discounted=discounted,
        rrp=rrp_val,
        rrp_currency=rrp_ccy,
    )

# -------------------- printing & CSV --------------------

CSV_COLS = ["asin","product_name","price","currency","buybox_exists","seller_name","seller_id","prime","discounted","rrp","rrp_currency","error"]

def fmt_bool(b: Optional[bool]) -> str:
    return "Yes" if b is True else "No" if b is False else "-"

def fmt_money(a: Optional[float], c: Optional[str]) -> str:
    return "-" if a is None else f"{a} {c or ''}".strip()

def print_vertical_table(row: Dict[str, Any]) -> None:
    """Clean, aligned vertical table for one ASIN."""
    label_vals = [
        ("ASIN", row.get("asin","-")),
        ("Title", shorten(row.get("product_name"), TITLE_MAX_TERM) or "-"),
        ("Price", fmt_money(row.get("price"), row.get("currency"))),
        ("Buy Box Exists", fmt_bool(row.get("buybox_exists"))),
        ("Seller", f"{row.get('seller_name') or '-'} (ID: {row.get('seller_id') or '-'})"),
        ("Prime", fmt_bool(row.get("prime"))),
        ("Discounted", fmt_bool(row.get("discounted"))),
        ("RRP", fmt_money(row.get("rrp"), row.get("rrp_currency"))),
    ]
    width = max(len(k) for k, _ in label_vals)
    line = "-" * (width + 2 + 40)
    print(line)
    for k, v in label_vals:
        print(f"{k:<{width}} : {v}")
    print(line)

def write_csv(rows: List[Dict[str, Any]], out_path: str) -> None:
    """Write CSV with a slightly shortened product_name for readability."""
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        w.writeheader()
        for r in rows:
            r = dict(r)
            r["product_name"] = shorten(r.get("product_name"), TITLE_MAX_CSV) or ""
            for c in CSV_COLS:
                r.setdefault(c, "")
            w.writerow(r)

def read_asins_from_csv(path: str) -> List[str]:
    asins: List[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            a = (row.get("asin") or row.get("ASIN") or "").strip()
            if a: asins.append(a)
    return asins

# -------------------- CLI --------------------

def main():
    ap = argparse.ArgumentParser(description="Rainforest Buy Box checker")
    ap.add_argument("--asin", help="Single ASIN (prints a clean vertical table)")
    ap.add_argument("--input-csv", help="CSV with column 'asin' (writes CSV)")
    ap.add_argument("--output-csv", default="rainforest_out.csv", help="Output CSV path for batch mode")
    ap.add_argument("--domain", default="amazon.co.uk", help="Amazon domain (e.g., amazon.com, amazon.de)")
    ap.add_argument("--env-file", default=".env.rainforest", help="Path to env file containing RAINFOREST_API_KEY")
    ap.add_argument("--workers", type=int, default=1, help="Parallel workers for CSV mode (default: 1)")
    args = ap.parse_args()

    if not args.asin and not args.input_csv:
        print("Provide --asin OR --input-csv", file=sys.stderr)
        sys.exit(2)

    load_dotenv(args.env_file)
    api_key = get_api_key()

    if args.asin:
        asin = args.asin.strip()
        try:
            data = fetch_asin(api_key, asin, args.domain)
            row = {"asin": asin, **data}
        except Exception as e:
            row = {"asin": asin, "error": str(e)}
        if row.get("error"):
            print(f"[ASIN {asin}] ERROR: {row['error']}")
        else:
            print_vertical_table(row)
        return

    # CSV mode with parallelism & order preserved
    asins = read_asins_from_csv(args.input_csv)

    def task(idx: int, a: str) -> Dict[str, Any]:
        try:
            d = fetch_asin(api_key, a, args.domain)
            d["asin"] = a
            d["_idx"] = idx
            return d
        except Exception as e:
            return {"asin": a, "error": str(e), "_idx": idx}

    rows: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = [ex.submit(task, i, a) for i, a in enumerate(asins)]
        for fut in as_completed(futures):
            rows.append(fut.result())

    rows.sort(key=lambda r: r.get("_idx", 0))
    for r in rows:
        r.pop("_idx", None)

    write_csv(rows, args.output_csb if hasattr(args, "output_csb") else args.output_csv)
    print(f"Wrote {len(rows)} row(s) to {args.output_csv}")

if __name__ == "__main__":
    main()