import csv
import os
import re
from datetime import date, datetime, timedelta
import openpyxl

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PHONES_XLSX_PATH = os.path.join(DATA_DIR, "phones.xlsx")
ORDERS_CSV_PATH = os.path.join(DATA_DIR, "orders.csv")
ORDERS_CSV_HEADER = [
    "Order Number",
    "Date and Time",
    "Product ID",
    "Model",
    "Variant",
    "Price (₹)",
    "Delivery Date",
]


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


def find_phone(model: str) -> list[dict] | str:
    """Finds up to 10 phones whose brand, model, and variant contain all asked words, joining the 3 sheets by Product ID."""
    loaded = _load_phone_sheets()
    if isinstance(loaded, str):
        return loaded
    info_by_id, pricing_by_id, avail_by_id = loaded

    words = (model or "").replace("/", " ").strip().lower().split()
    if not words:
        return []

    results: list[dict] = []
    for pid, info in info_by_id.items():
        brand = str(info.get("Brand") or "").strip()
        model_name = str(info.get("Model") or "").strip()
        variant = str(info.get("Variant (RAM / Storage)") or "").strip()
        searchable = f"{brand} {model_name} {variant}".replace("/", " ").lower()
        if not all(word in searchable for word in words):
            continue

        pricing = pricing_by_id.get(pid, {})
        avail = avail_by_id.get(pid, {})

        selling_price = pricing.get("Selling Price (₹)")
        delivery_days = avail.get("Delivery (days)")

        results.append(
            {
                "product_id": pid,
                "model": _format_display_model(brand, model_name),
                "variant": variant,
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


def _load_phone_sheets() -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]] | str:
    """Loads the three phone sheets keyed by Product ID, or returns an error message."""
    if not os.path.exists(PHONES_XLSX_PATH):
        return "The phone catalogue could not be opened: data/phones.xlsx was not found."
    try:
        wb = openpyxl.load_workbook(PHONES_XLSX_PATH, read_only=True, data_only=True)
    except Exception as exc:
        return f"The phone catalogue could not be opened: {exc}"
    try:
        info_by_id = _read_sheet_by_id(wb["Product Information"])
        pricing_by_id = _read_sheet_by_id(wb["Product Pricing"])
        avail_by_id = _read_sheet_by_id(wb["Product Availability"])
    except Exception as exc:
        return f"The phone catalogue could not be opened: {exc}"
    finally:
        wb.close()
    return info_by_id, pricing_by_id, avail_by_id


def _format_display_model(brand: str, model_name: str) -> str:
    if brand and brand.lower() not in model_name.lower():
        return f"{brand} {model_name}".strip()
    return model_name


def _format_date(d: date | datetime) -> str:
    return f"{d.day} {d.strftime('%B %Y')}"


def list_phones(brand: str, in_stock_only: bool = False) -> list[dict] | str:
    """Lists up to 10 phones of a brand from data/phones.xlsx, cheapest first."""
    loaded = _load_phone_sheets()
    if isinstance(loaded, str):
        return loaded
    info_by_id, pricing_by_id, avail_by_id = loaded

    brand_q = (brand or "").strip().lower()
    if not brand_q or not info_by_id:
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


def check_delivery(product_id: str, today: date | datetime | None = None) -> dict | str:
    """Returns delivery days and arrival date (or restock date if out of stock) for one product ID."""
    loaded = _load_phone_sheets()
    if isinstance(loaded, str):
        return loaded
    info_by_id, _, avail_by_id = loaded

    pid_q = (product_id or "").strip()
    if not pid_q:
        return {"error": "Product ID not found."}
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


def _lookup_orderable_phone(
    product_id: str, today: date | datetime | None = None
) -> dict | str:
    """Looks up a phone for ordering; returns order summary dict or an error string."""
    loaded = _load_phone_sheets()
    if isinstance(loaded, str):
        return loaded
    info_by_id, pricing_by_id, avail_by_id = loaded

    pid_q = (product_id or "").strip()
    if not pid_q:
        return "Product ID not found."
    if not info_by_id:
        return "Phone catalogue not found."

    matched_pid = pid_q if pid_q in info_by_id else next(
        (k for k in info_by_id if k.lower() == pid_q.lower()), None
    )
    if not matched_pid:
        return f"Product ID '{pid_q}' not found."

    info = info_by_id[matched_pid]
    pricing = pricing_by_id.get(matched_pid, {})
    avail = avail_by_id.get(matched_pid, {})

    brand = str(info.get("Brand") or "").strip()
    model_name = str(info.get("Model") or "").strip()
    display_model = _format_display_model(brand, model_name)
    variant = str(info.get("Variant (RAM / Storage)") or "").strip()
    status = str(avail.get("Status") or "").strip()

    if status.lower() == "out of stock":
        restock_raw = avail.get("Restock Date")
        if isinstance(restock_raw, (datetime, date)):
            restock_str = _format_date(restock_raw)
        else:
            restock_str = str(restock_raw or "").strip()
        if restock_str:
            return f"{display_model} ({variant}) is out of stock (restock {restock_str}) and cannot be ordered."
        return f"{display_model} ({variant}) is out of stock and cannot be ordered."

    if status.lower() not in ("in stock", "low stock"):
        return f"{display_model} ({variant}) is currently '{status}' and cannot be ordered."

    selling_price = pricing.get("Selling Price (₹)")
    price_int = int(selling_price) if selling_price is not None else 0

    now = today if isinstance(today, datetime) else datetime.now()
    today_d = today.date() if isinstance(today, datetime) else (today or now.date())
    delivery_raw = avail.get("Delivery (days)")
    if isinstance(delivery_raw, (int, float)):
        arrival_date = _format_date(today_d + timedelta(days=int(delivery_raw)))
    else:
        arrival_date = ""

    return {
        "product_id": matched_pid,
        "model": display_model,
        "variant": variant,
        "price_rupees": price_int,
        "status": status,
        "delivery_date": arrival_date,
    }


def get_phone_summary(
    product_id: str, today: date | datetime | None = None
) -> dict | str:
    """Returns phone details needed to confirm an order, or an error string."""
    return _lookup_orderable_phone(product_id, today=today)


def _next_order_number(csv_path: str) -> str:
    """Returns the next sequential order number (ORD-0001, ORD-0002, ...)."""
    if not os.path.exists(csv_path):
        return "ORD-0001"
    max_num = 0
    row_count = 0
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return "ORD-0001"
        for row in reader:
            if not row:
                continue
            row_count += 1
            m = re.match(r"^ORD-(\d+)$", row[0].strip(), re.IGNORECASE)
            if m:
                max_num = max(max_num, int(m.group(1)))
    next_num = max(max_num, row_count) + 1
    return f"ORD-{next_num:04d}"


def place_order(
    product_id: str, today: date | datetime | None = None
) -> dict | str:
    """Places an order for an in-stock or low-stock phone by appending a row to data/orders.csv."""
    summary = _lookup_orderable_phone(product_id, today=today)
    if isinstance(summary, str):
        return summary

    now = today if isinstance(today, datetime) else datetime.now()
    order_datetime = now.strftime("%Y-%m-%d %H:%M:%S")

    os.makedirs(os.path.dirname(ORDERS_CSV_PATH), exist_ok=True)
    file_exists = os.path.exists(ORDERS_CSV_PATH) and os.path.getsize(ORDERS_CSV_PATH) > 0
    order_number = _next_order_number(ORDERS_CSV_PATH)

    with open(ORDERS_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(ORDERS_CSV_HEADER)
        writer.writerow(
            [
                order_number,
                order_datetime,
                summary["product_id"],
                summary["model"],
                summary["variant"],
                summary["price_rupees"],
                summary["delivery_date"],
            ]
        )

    return {
        "order_number": order_number,
        "date_time": order_datetime,
        "product_id": summary["product_id"],
        "model": summary["model"],
        "variant": summary["variant"],
        "price_rupees": summary["price_rupees"],
        "delivery_date": summary["delivery_date"],
    }

