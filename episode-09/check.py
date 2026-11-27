from bot import ask, new_chat

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


def run_checks() -> None:
    passed = 0
    total_checks = len(CHECKS)

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

    print(f"{passed} of {total_checks} passed", flush=True)


if __name__ == "__main__":
    run_checks()

