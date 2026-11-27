import os
from datetime import date, datetime, timedelta
import openpyxl

PHONES_XLSX_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "phones.xlsx"
)


def _read_sheet_by_id(ws) -> dict[str, dict]:
    """Reads a worksheet into a dict keyed by Product ID using its header row."""
    rows_iter = ws.iter_rows(values_only=True)
    headers = next(rows_iter, None)
    if not headers:
        return {}
    header_list = [str(h).strip() if h is not None else "" for h in headers]
    by_id: dict[str, dict] = {}
    for row in rows_iter:
        if not row or row[0] is None:
            continue
        pid = str(row[0]).strip()
        if not pid:
            continue
        by_id[pid] = {
            header_list[i]: row[i]
            for i in range(min(len(header_list), len(row)))
        }
    return by_id


def find_phone(model: str) -> list[dict]:
    """Finds up to 10 phones whose model name contains all asked words, joining the 3 sheets by Product ID."""
    words = (model or "").strip().lower().split()
    if not words or not os.path.exists(PHONES_XLSX_PATH):
        return []

    wb = openpyxl.load_workbook(PHONES_XLSX_PATH, read_only=True, data_only=True)
    try:
        info_by_id = _read_sheet_by_id(wb["Product Information"])
        pricing_by_id = _read_sheet_by_id(wb["Product Pricing"])
        avail_by_id = _read_sheet_by_id(wb["Product Availability"])
    finally:
        wb.close()

    results: list[dict] = []
    for pid, info in info_by_id.items():
        brand = str(info.get("Brand") or "").strip()
        model_name = str(info.get("Model") or "").strip()
        searchable = f"{brand} {model_name}".lower()
        if not all(word in searchable for word in words):
            continue

        pricing = pricing_by_id.get(pid, {})
        avail = avail_by_id.get(pid, {})

        selling_price = pricing.get("Selling Price (₹)")
        delivery_days = avail.get("Delivery (days)")

        display_model = (
            f"{brand} {model_name}".strip()
            if brand and brand.lower() not in model_name.lower()
            else model_name
        )

        results.append(
            {
                "model": display_model,
                "variant": str(info.get("Variant (RAM / Storage)") or "").strip(),
                "selling_price_rupees": int(selling_price) if selling_price is not None else 0,
                "status": str(avail.get("Status") or "").strip(),
                "delivery_days": int(delivery_days)
                if isinstance(delivery_days, (int, float))
                else delivery_days,
            }
        )
        if len(results) >= 10:
            break

    return results


def _load_phone_sheets() -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    """Loads the three phone sheets keyed by Product ID."""
    if not os.path.exists(PHONES_XLSX_PATH):
        return {}, {}, {}
    wb = openpyxl.load_workbook(PHONES_XLSX_PATH, read_only=True, data_only=True)
    try:
        info_by_id = _read_sheet_by_id(wb["Product Information"])
        pricing_by_id = _read_sheet_by_id(wb["Product Pricing"])
        avail_by_id = _read_sheet_by_id(wb["Product Availability"])
    finally:
        wb.close()
    return info_by_id, pricing_by_id, avail_by_id


def _format_display_model(brand: str, model_name: str) -> str:
    if brand and brand.lower() not in model_name.lower():
        return f"{brand} {model_name}".strip()
    return model_name


def _format_date(d: date | datetime) -> str:
    return f"{d.day} {d.strftime('%B %Y')}"


def list_phones(brand: str, in_stock_only: bool = False) -> list[dict]:
    """Lists up to 10 phones of a brand from data/phones.xlsx, cheapest first."""
    brand_q = (brand or "").strip().lower()
    if not brand_q:
        return []

    info_by_id, pricing_by_id, avail_by_id = _load_phone_sheets()
    if not info_by_id:
        return []

    results: list[dict] = []
    for pid, info in info_by_id.items():
        row_brand = str(info.get("Brand") or "").strip()
        if row_brand.lower() != brand_q:
            continue

        avail = avail_by_id.get(pid, {})
        status = str(avail.get("Status") or "").strip()
        if in_stock_only and status.lower() == "out of stock":
            continue

        pricing = pricing_by_id.get(pid, {})
        selling_price = pricing.get("Selling Price (₹)")
        model_name = str(info.get("Model") or "").strip()

        results.append(
            {
                "product_id": pid,
                "model": _format_display_model(row_brand, model_name),
                "variant": str(info.get("Variant (RAM / Storage)") or "").strip(),
                "selling_price_rupees": int(selling_price) if selling_price is not None else 0,
                "status": status,
            }
        )

    results.sort(key=lambda r: r["selling_price_rupees"])
    return results[:10]


def check_delivery(product_id: str, today: date | datetime | None = None) -> dict:
    """Returns delivery days and arrival date (or restock date if out of stock) for one product ID."""
    pid_q = (product_id or "").strip()
    if not pid_q:
        return {"error": "Product ID not found."}

    info_by_id, _, avail_by_id = _load_phone_sheets()
    if not info_by_id:
        return {"error": "Phone catalogue not found."}

    matched_pid = pid_q if pid_q in info_by_id else next(
        (k for k in info_by_id if k.lower() == pid_q.lower()), None
    )
    if not matched_pid:
        return {"error": f"Product ID '{pid_q}' not found."}

    info = info_by_id[matched_pid]
    avail = avail_by_id.get(matched_pid, {})
    brand = str(info.get("Brand") or "").strip()
    model_name = str(info.get("Model") or "").strip()
    variant = str(info.get("Variant (RAM / Storage)") or "").strip()
    status = str(avail.get("Status") or "").strip()

    base = {
        "product_id": matched_pid,
        "model": _format_display_model(brand, model_name),
        "variant": variant,
        "status": status,
    }

    if status.lower() == "out of stock":
        restock_raw = avail.get("Restock Date")
        if isinstance(restock_raw, (datetime, date)):
            restock_str = _format_date(restock_raw)
        else:
            restock_str = str(restock_raw or "").strip()
        base["restock_date"] = restock_str
        return base

    today_d = today.date() if isinstance(today, datetime) else (today or datetime.now().date())
    delivery_raw = avail.get("Delivery (days)")
    if isinstance(delivery_raw, (int, float)):
        days = int(delivery_raw)
        arrives = today_d + timedelta(days=days)
        base["delivery_days"] = days
        base["arrival_date"] = _format_date(arrives)
    else:
        base["delivery_days"] = delivery_raw
        base["arrival_date"] = ""

    return base

