# Chatbot Series - 10 An Agent We Can Trust (honest errors, a yes before an order)

A chatbot application powered by the Google GenAI SDK (`gemini-3.1-flash-lite`). It includes a desktop GUI window (`ui.py`) built with Tkinter featuring customizable generation settings (Temperature, Top-P, Max tokens), short-term memory (sliding exchange window), long-term memory (running summary of older exchanges), selectable and editable character prompt styles (`examples`, `role`, `step-by-step`, `shop-assistant`) loaded from `prompts/system/`, dynamic date and time injection (`Today is <weekday, day month year>, <time>.`), shop context stuffing (`shop.py` processing PDF, HTML, MD, TXT from `prompts/shop/`), structured answers (Gemini fills a Pydantic shape, and our code adds up the total), a regression test (`check.py`), three phone tools (`find_phone`, `list_phones`, `check_delivery` in `tools.py`, on the 500-phone workbook `data/phones.xlsx`) run by our own code in a loop with a step cap, tool errors returned as text, and `place_order` behind a Yes / No box our code shows: an agent we can trust, as well as a terminal interface (`bot.py`), speech bubbles, token tracking, and error handling.

## Project Structure

```text
├── ui.py              # Desktop window (frontend with Tkinter)
├── bot.py             # Chatbot backend with ask(), new_chat(), usage(), and terminal chat loop
├── shop.py            # Preprocessor for shop files (PDF, HTML, MD, TXT into plain text shop sheet)
├── tools.py           # find_phone, list_phones, check_delivery and place_order; errors returned as text
├── check.py           # Regression test: 10 checks against our answer key, PASS or FAIL
├── data/
│   ├── phones.xlsx    # 500 phones in 3 sheets: Product Information, Pricing, Availability (invented prices)
│   └── orders.csv     # made by place_order on the first order (not shipped: you start with no orders)
├── prompts/           # Prompts and UI sketch
│   ├── 01-api-key.txt
│   ├── 02-terminal-chat.txt
│   ├── 02-window.txt
│   ├── 03-settings.txt
│   ├── 04-memory.txt
│   ├── 04-summary.txt
│   ├── 05-character.txt
│   ├── 05-styles.txt
│   ├── 06-date.txt
│   ├── 06-shop.txt
│   ├── 07-structured.txt
│   ├── 07-check.txt
│   ├── 08-tool.txt
│   ├── 09-agent.txt
│   ├── 09-structured-last.txt
│   ├── 10-honest-tools.txt
│   ├── 10-order.txt
│   ├── 10-check.txt
│   ├── system/
│   │   ├── agent.txt           # How Volt works with tools: Plan, Execute, Evaluate, Iterate; never guess when a tool fails (typed by hand)
│   │   ├── examples.txt        # Role + 3 example Q&As (default)
│   │   ├── role.txt            # 2-line role definition
│   │   ├── step-by-step.txt    # Role + 4-step answering methodology
│   │   └── shop-assistant.txt  # General shop assistant persona
│   ├── shop/
│   │   ├── faq.md              # Frequently asked questions
│   │   ├── offers.html         # Weekly offers
│   │   ├── products.pdf        # Products and prices
│   │   └── returns.txt         # Return policy
│   └── ui-sketch.png
├── .env               # Environment file containing GEMINI_API_KEY (ignored by git)
├── .gitignore         # Git ignore rules for .env, .venv, etc.
├── requirements.txt   # Python dependencies
└── README.md          # Setup and execution guide
```

## What episode 10 adds

**Honest tools.** Before, a missing workbook made `find_phone` and `list_phones` return an empty list, the same answer as "no such phone", so Volt told a customer we do not sell a phone we sell. Now every tool returns an error as text when `data/phones.xlsx` cannot be opened ("The phone catalogue could not be opened: ..."). `find_phone` also searches the variant: a search for "Galaxy S25 12GB/256GB" used to find nothing.

**Errors reach Volt.** `bot.py` runs every tool inside a `try`. When a tool fails, its message goes back to Gemini as the tool's result, and the loop carries on. The window shows the error in the step's grey line. One line typed by hand at the end of `prompts/system/agent.txt`: "If a tool returns an error, tell the customer you could not check, and never guess."

**A tool that acts.** `place_order(product_id)` adds one row to `data/orders.csv` (order number ORD-0001, ORD-0002 ..., date and time, Product ID, model, variant, price, delivery date) and never changes `data/phones.xlsx`. An out-of-stock phone is refused with an error as text. `find_phone` now returns the Product ID that it needs.

**A yes before an order.** Before `place_order` runs, our code stops and the window asks "Place this order?" with the phone, variant, price and delivery date, and Yes / No. Only Yes runs it. On No, Gemini is told "The customer said no. No order was placed." With no Yes / No function (as in `check.py`), the answer is No. It cannot be switched off in Settings. When you say No, no total is shown under the reply.

**Try it.** Rename `data/phones.xlsx` and ask "How much is the Galaxy S25 with 12GB / 256GB?": the grey line shows the error and Volt does not invent an answer. Rename it back: 69,999, in stock. Then "Order the Galaxy S25 with 12GB / 256GB for me." and answer No, then Yes: ORD-0001, and one row in `data/orders.csv`.

**The regression test grows.** `check.py` now has 10 checks: the 8 from episode 9, check 9 (the workbook hidden for that check only: no price, and no "we don't sell it") and check 10 (an order answered No: `orders.csv` unchanged). `python check.py` prints `10 of 10 passed`.

**How it was built.** `prompts/10-honest-tools.txt`, `prompts/10-order.txt` and `prompts/10-check.txt` were given to the agent in Antigravity, on Gemini 4 Hydrogen with Thinking effort Medium. Pick the model your Antigravity offers. One change after the recording: no total is shown under a cancelled order.
