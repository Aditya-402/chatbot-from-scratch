import os
from bot import ask, new_chat
from tools import PHONES_XLSX_PATH, ORDERS_CSV_PATH

CHECKS = [
    ("How much is the 20W charger?", 899),
    ("How much is the charger with a cable this week?", 949),
    ("How much are two 2 m USB-C cables?", 898),
    ("How much are wireless earbuds and a phone stand together?", 2848),
    ("How much is a smart watch?", 0),
    ("How much is the Galaxy S25 with 12GB / 256GB?", 69999),
    ("How much is the Pixel 9?", 0),
    ("Which is the cheapest Samsung phone in stock, and when can it be delivered?", 7999),
]


def _read_orders_snapshot() -> list[str] | None:
    if not os.path.exists(ORDERS_CSV_PATH):
        return None
    with open(ORDERS_CSV_PATH, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def run_checks() -> None:
    passed = 0
    total_checks = len(CHECKS) + 2

    for i, (question, expected_total) in enumerate(CHECKS, start=1):
        new_chat()
        try:
            result = ask(
                question,
                structured_answers=True,
                today_date=True,
                shop_files=True,
            )
            volt_total = sum(item.price_rupees * item.quantity for item in result.items)
        except Exception:
            volt_total = "ERROR"

        status = "PASS" if volt_total == expected_total else "FAIL"
        if status == "PASS":
            passed += 1

        print(
            f"{i:<3} {question:<62} {volt_total:<12} {expected_total:<12} {status}",
            flush=True,
        )

    # Check 9: missing workbook
    q9 = "How much is the Galaxy S25 with 12GB / 256GB?"
    hidden_path = f"{PHONES_XLSX_PATH}.hidden"
    renamed = False
    new_chat()
    try:
        if os.path.exists(PHONES_XLSX_PATH):
            os.rename(PHONES_XLSX_PATH, hidden_path)
            renamed = True
        result9 = ask(
            q9,
            structured_answers=True,
            today_date=True,
            shop_files=True,
        )
        volt_total9 = sum(item.price_rupees * item.quantity for item in result9.items)
        reply9_lower = (result9.reply or "").lower()
        claims_not_sold = any(
            phrase in reply9_lower
            for phrase in ("don't sell", "do not sell", "don't carry", "do not carry")
        )
        ok9 = volt_total9 == 0 and not claims_not_sold
    except Exception:
        volt_total9 = "ERROR"
        ok9 = False
    finally:
        if renamed and os.path.exists(hidden_path) and not os.path.exists(PHONES_XLSX_PATH):
            os.rename(hidden_path, PHONES_XLSX_PATH)

    status9 = "PASS" if ok9 else "FAIL"
    if ok9:
        passed += 1
    print(
        f"{9:<3} {q9:<62} {volt_total9:<12} {0:<12} {status9}",
        flush=True,
    )

    # Check 10: order without a yes
    q10 = "Order the Galaxy S25 with 12GB / 256GB for me."
    orders_before = _read_orders_snapshot()
    new_chat()
    try:
        ask(
            q10,
            structured_answers=True,
            today_date=True,
            shop_files=True,
            confirm_order=lambda _info: False,
        )
        orders_after = _read_orders_snapshot()
        ok10 = orders_before == orders_after
        actual10 = len(orders_after) if orders_after is not None else 0
    except Exception:
        actual10 = "ERROR"
        ok10 = False

    expected10 = len(orders_before) if orders_before is not None else 0
    status10 = "PASS" if ok10 else "FAIL"
    if ok10:
        passed += 1
    print(
        f"{10:<3} {q10:<62} {actual10:<12} {expected10:<12} {status10}",
        flush=True,
    )

    print(f"{passed} of {total_checks} passed", flush=True)


if __name__ == "__main__":
    run_checks()

