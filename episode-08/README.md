# Chatbot Series - 08 The First Tool (find_phone)

A chatbot application powered by the Google GenAI SDK (`gemini-3.1-flash-lite`). It includes a desktop GUI window (`ui.py`) built with Tkinter featuring customizable generation settings (Temperature, Top-P, Max tokens), short-term memory (sliding exchange window), long-term memory (running summary of older exchanges), selectable and editable character prompt styles (`examples`, `role`, `step-by-step`, `shop-assistant`) loaded from `prompts/system/`, dynamic date and time injection (`Today is <weekday, day month year>, <time>.`), shop context stuffing (`shop.py` processing PDF, HTML, MD, TXT from `prompts/shop/`), structured answers (Gemini fills a Pydantic shape, and our code adds up the total), a regression test (`check.py`), its first tool (`find_phone` in `tools.py`, run by our own code on the 500-phone workbook `data/phones.xlsx`), as well as a terminal interface (`bot.py`), speech bubbles, token tracking, and error handling.

## Project Structure

```text
├── ui.py              # Desktop window (frontend with Tkinter)
├── bot.py             # Chatbot backend with ask(), new_chat(), usage(), and terminal chat loop
├── shop.py            # Preprocessor for shop files (PDF, HTML, MD, TXT into plain text shop sheet)
├── tools.py           # The first tool: find_phone(model) joins the 3 sheets of data/phones.xlsx by Product ID
├── check.py           # Regression test: 7 fixed questions against our answer key, PASS or FAIL
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
│   ├── system/
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

## What episode 8 adds

**The first tool.** `tools.py` has one function, `find_phone(model)`. It finds every phone whose model name contains all the words asked, joins the 3 sheets of `data/phones.xlsx` (Product Information, Product Pricing, Product Availability) by Product ID, and returns at most 10 short rows: model, variant, selling price in rupees, status and delivery days.

**Our own code runs the call.** `bot.py` describes `find_phone` to Gemini as a tool (`types.Tool` with one `FunctionDeclaration`: "look up a phone's price and stock by its model name", one input, `model`). Automatic function calling is not used: when Gemini answers with a function call, our code runs `find_phone`, sends the rows back with `types.Part.from_function_response(...)`, and asks Gemini again, at most a few rounds. The model never runs anything; our code does. When `find_phone` returns no rows, Volt says we don't sell that phone and never invents a price. Structured answers keep working.

**The tool line.** Under a reply that used the tool, the window shows a grey line such as `Tool: find_phone("Galaxy S25") -> 10 rows`. `Settings > Phone lookup` turns the tool on or off (on by default; off = Volt has no tool and says it will check with the shop). The status line shows `Phone lookup: on`.

**Why `phones.txt` is gone.** In episode 7 the 500 phones were stuffed into the shop sheet as text: about 42,600 tokens in for every question, and one stock answer came back wrong. In this episode the file is deleted and the phones live only in the workbook. The same 3 questions cost 8,936 tokens in with the tool (against about 128,000), about 14 times less, and all 3 answers are right.

**The regression test grows.** `check.py` now has 7 checks: the 5 from episode 7 plus the Galaxy S25 12GB / 256GB (69999) and the Pixel 9 (0, we don't sell it). `python check.py` prints `7 of 7 passed`.

**How it was built.** The prompt `prompts/08-tool.txt` was given to the agent in Antigravity. Antigravity updated itself while we recorded (Gemini 4 Hydrogen became available, Gemini 3.8 Flash was leaving and stopped with an error), so the agent ran on Gemini 4 Hydrogen with Thinking effort Medium. Pick the model your Antigravity offers. The agent also ran `check.py` on its own to check its work.

**Still here from episode 7.** `prompts/shop/offers.html` and the key in `check.py` say 949 for the charger with a cable (the live price change of episode 7).

## Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher installed.

### 2. Activate the Virtual Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.\.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 3. Configure Environment Variables

Ensure `.env` contains your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run the Desktop Window (GUI)

Launch the desktop chatbot window:
```bash
python ui.py
```

- **Menu Bar & Settings**:
  - `Settings > Temperature...`: Slider from 0 to 2, step 0.1 (default 1.0).
  - `Settings > Top-P...`: Slider from 0 to 1, step 0.05 (default 0.95).
  - `Settings > Max tokens...`: Slider from 10 to 2000, step 10 (default 2000).
  - `Settings > Top-K: 64 (fixed for this model)`: Displayed greyed out.
  - `Settings > Short-term memory`: Toggle tick option to enable or disable sliding window memory (starts selected).
  - `Settings > Memory window...`: Dialog to select window size (choice of 0, 3, 6, 9, 12, or 15 exchanges; starts at 6).
  - `Settings > Long-term memory`: Toggle tick option to enable or disable running summary memory (starts selected).
  - `Settings > Show memory summary`: Opens a small window showing the current running summary of older exchanges.
  - `Settings > Character`: Toggle tick option to enable or disable the shop assistant system prompt (starts selected).
  - `Settings > Character version`: Submenu offering a choice of the versions found in `prompts/system/` (`examples`, `role`, `step-by-step`, `shop-assistant`).
  - `Settings > Edit character...`: Opens a window showing the current version's text, an editable area, a **Save** button (which saves the file and uses the text from the next question on), and a **Cancel** button.
  - `Settings > Today's date`: Toggle tick option to enable or disable prepending today's date and time line (`Today is <weekday, day month year>, <time>.`) before the system prompt (starts selected).
  - `Settings > Shop files`: Toggle tick option to enable or disable sending the shop sheet into the system instruction (starts selected).
  - `Settings > Show shop sheet`: Opens a window displaying the combined shop sheet text that the bot receives.
  - `Settings > Reload shop files`: Re-reads shop files from `prompts/shop/` and updates the shop sheet and token counts on the fly.
  - `Settings > Structured answers`: Toggle tick option: Gemini answers in the `Answer` shape and the window shows `Total (our code): N rupees` under the reply (starts selected).
  - `Settings > Phone lookup`: Toggle tick option: Volt may call `find_phone` on `data/phones.xlsx`; each call shows on a grey tool line under the reply (starts selected).
  - `Settings > New chat`: Empties the chat history and running summary in `bot.py` and clears the chat area (keeps the chosen character version).
  - `Settings > Reset to defaults`: Reverts all settings (including memory, character toggle, character version, today's date, and shop files toggle) back to starting defaults.
- **Settings & Status Line**: Small grey line under the menu bar displaying active parameters, memory state, character version, date status, and shop status (e.g., `Temperature 1.0 · Top-P 0.95 · Max tokens 2000 · Short-term on, 3 exchanges, 3 in the window. Long-term on, 5 summarised · Character: Volt (examples) · Date: on · Shop: 4 files, 329 tokens · Phone lookup: on`).
- **Chat Area**: Read-only with selectable and copyable text.
- **Bubbles**: User queries on the left in plum (`#5a3d5c`) and bot replies on the right in ink (`#2b2730`).
- **Reply Metadata Line**: Under each reply, displays tokens in/out, settings used, and `"stopped: max tokens"` when the response was cut short.
- **Token Counter**: Top-right badge showing cumulative tokens (including tokens from running summary updates and system instructions); hover to inspect tokens in, tokens out, and cost.
- **Typing & Sending**: Type in the bottom input box and click **Send** or press **Enter**.
- **Error Handling**: Graceful error notifications (e.g. 429 quota exhaustion, 503 unavailability, or internet disconnection) in clay (`#a8441f`).

### 5. Run the Terminal Chat

Run the terminal chat loop:
```bash
python bot.py
```

- Type your question when prompted (`You: `).
- The chatbot replies (`Bot: `) with the Volt character (`examples` style by default), retains both short-term memory (last 6 exchanges) and long-term memory (running summary of exchanges falling outside the window), and includes today's date/time and shop sheet across questions using default settings.
- Type `exit` or `bye` to end the session.

### 6. Run the Regression Test

```bash
python check.py
```

Seven lines, each with the question, Volt's total, our expected total and PASS or FAIL, then `N of 7 passed`. Edit the `CHECKS` list at the top to add your own questions and the totals you expect.

### 7. Backend Functions

- `ask(question, temperature=1.0, top_p=0.95, max_output_tokens=2000, short_term_memory=True, memory_window=6, long_term_memory=True, character=True, character_version="examples", today_date=True, shop_files=True, structured_answers=True, phone_lookup=True)`: Sends system instruction combining today's date line (if enabled), character prompt (if enabled), and shop sheet (if enabled), summary first (if present), up to the last $N$ exchanges from history, then the new question to Gemini. Updates the running summary for exchanges falling outside the window, and returns an `AskResult` with reply text, the structured `items` (when structured answers are on), token usage `(tokens_in, tokens_out)`, and stopped reason.
- `get_character_versions()`: Returns a list of character versions available in `prompts/system/`.
- `load_system_prompt(version="examples")`: Reads and returns the content of `prompts/system/<version>.txt`.
- `save_system_prompt(version, text)`: Saves edited text to `prompts/system/<version>.txt`.
- `get_character_status(character=True, version="examples")`: Returns the status string (e.g., `Character: Volt (examples)` or `Character: off`).
- `get_date_status(today_date=True)`: Returns the date status string (e.g., `Date: on` or `Date: off`).
- `get_today_date_line(now=None)`: Returns `'Today is <weekday, day month year>, <time>.'` formatted at the moment of the call.
- `reload_shop_files()`: Re-reads `prompts/shop/` files, rebuilds the shop sheet, and recalculates file count and tokens.
- `get_current_shop_sheet()`: Returns the cached plain text shop sheet.
- `get_shop_files_count()`: Returns the count of loaded shop files.
- `get_shop_tokens_count()`: Returns the token count for the shop sheet.
- `find_phone(model)` (in `tools.py`): Returns up to 10 joined rows (model, variant, selling_price_rupees, status, delivery_days) for phones whose model name contains all the words asked.
- `get_phone_lookup_status(phone_lookup=True)`: Returns `Phone lookup: on` or `Phone lookup: off`.
- `get_shop_status(shop_files=True)`: Returns the shop status string (e.g., `Shop: 4 files, 331 tokens` or `Shop: off`).
- `new_chat()`: Empties the in-memory chat history list and clears the running summary.
- `get_summary()`: Returns the current running summary string.
- `get_summarized_count()`: Returns the number of exchanges summarized so far.
- `usage()`: Returns the cumulative totals for the current run: `(tokens_in, tokens_out, cost_in_dollars)`.
