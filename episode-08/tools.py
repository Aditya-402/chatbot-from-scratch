import os
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

