# Chatbot Series - 09 The First Agent (a loop with a step cap)

A chatbot application powered by the Google GenAI SDK (`gemini-3.1-flash-lite`). It includes a desktop GUI window (`ui.py`) built with Tkinter featuring customizable generation settings (Temperature, Top-P, Max tokens), short-term memory (sliding exchange window), long-term memory (running summary of older exchanges), selectable and editable character prompt styles (`examples`, `role`, `step-by-step`, `shop-assistant`) loaded from `prompts/system/`, dynamic date and time injection (`Today is <weekday, day month year>, <time>.`), shop context stuffing (`shop.py` processing PDF, HTML, MD, TXT from `prompts/shop/`), structured answers (Gemini fills a Pydantic shape, and our code adds up the total), a regression test (`check.py`), three phone tools (`find_phone`, `list_phones`, `check_delivery` in `tools.py`, on the 500-phone workbook `data/phones.xlsx`) run by our own code in a loop with a step cap: our first agent, as well as a terminal interface (`bot.py`), speech bubbles, token tracking, and error handling.

## Project Structure

```text
├── ui.py              # Desktop window (frontend with Tkinter)
├── bot.py             # Chatbot backend with ask(), new_chat(), usage(), and terminal chat loop
├── shop.py            # Preprocessor for shop files (PDF, HTML, MD, TXT into plain text shop sheet)
├── tools.py           # find_phone, list_phones (cheapest first) and check_delivery, on data/phones.xlsx
├── check.py           # Regression test: 8 fixed questions against our answer key, PASS or FAIL
├── data/
│   └── phones.xlsx    # 500 phones in 3 sheets: Product Information, Pricing, Availability (invented prices)
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
│   ├── system/
│   │   ├── agent.txt           # How Volt works with tools: Plan, Execute, Evaluate, Iterate (typed by hand)
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

## What episode 9 adds

**More tools.** `tools.py` keeps `find_phone(model)` and adds two: `list_phones(brand, in_stock_only)` returns a brand's phones cheapest first (at most 10 rows, with the Product ID; Low stock still counts as in stock), and `check_delivery(product_id)` returns the status, the delivery days and the date it arrives (today plus the days), or the restock date when it is out of stock.

**A loop our own code runs.** `bot.py` describes the 3 tools to Gemini. Our code asks Gemini, runs the tool it asks for, sends the result back and asks again, one step at a time, until Volt answers without a tool. Every call to Gemini is one step. The window shows one grey line per tool call (`Step 1: list_phones("Samsung", in stock) -> 10 rows`) and a last line `Steps: N of M`.

**The step cap.** `DEFAULT_STEP_CAP = 6` in `bot.py`, changed in `Settings > Step cap` (1 to 10). At the cap our code stops Volt and the reply is "I couldn't finish this in N steps. Please ask again or raise the step cap." The prompt cannot override it: it is our code's brake.

**The agent prompt.** `prompts/system/agent.txt` was typed by hand: Plan, Execute, Evaluate, Iterate (a common pattern for agents, not one formal standard), never invent a price, a stock status or a date. Two more lines were added later (tools only for phones; the list is cheapest first). It is added to the system prompt whenever Phone lookup is on. The prompt only asks; the loop in our code does the work.

**Structured answers once, at the end.** With structured answers (the JSON reply of episode 7) on every call together with the tools, Gemini kept calling tools and hit the step cap. So the second prompt, `prompts/09-structured-last.txt`, makes the loop run in plain text; when Volt has answered, one last call with no tools turns that answer into the reply and items (not a step; its tokens count in the tokens in).

**One sentence by hand.** The last call's items rule says: use the price you said in your answer; an offer for products sold together is one item at that price (the charger with a cable, 949).

**Try it.** "Which is the cheapest Samsung phone in stock, and when can it be delivered?" takes 2 tool steps (the Galaxy A06 2GB / 32GB, 7,999, 2 days). "I need a Samsung phone delivered by tomorrow. Which is the cheapest?" checks the phones one by one and stops at the Galaxy M06 5G 4GB / 64GB, 9,999, in 5 of 6 steps.

**The regression test grows.** `check.py` now has 8 checks: the 7 from episode 8 plus the cheapest Samsung in stock (7999). `python check.py` prints `8 of 8 passed`.

**How it was built.** `prompts/09-agent.txt` and then `prompts/09-structured-last.txt` were given to the agent in Antigravity, on Gemini 4 Hydrogen with Thinking effort Medium. Pick the model your Antigravity offers. The agent also ran `check.py` on its own to check its work.
