# Chatbot Series - 07 Structured Output & a Regression Test

A chatbot application powered by the Google GenAI SDK (`gemini-3.1-flash-lite`). It includes a desktop GUI window (`ui.py`) built with Tkinter featuring customizable generation settings (Temperature, Top-P, Max tokens), short-term memory (sliding exchange window), long-term memory (running summary of older exchanges), selectable and editable character prompt styles (`examples`, `role`, `step-by-step`, `shop-assistant`) loaded from `prompts/system/`, dynamic date and time injection (`Today is <weekday, day month year>, <time>.`), shop context stuffing (`shop.py` processing PDF, HTML, MD, TXT from `prompts/shop/`), structured answers (Gemini fills a Pydantic shape, and our code adds up the total), a regression test (`check.py`), as well as a terminal interface (`bot.py`), speech bubbles, token tracking, and error handling.

## Project Structure

```text
├── ui.py              # Desktop window (frontend with Tkinter)
├── bot.py             # Chatbot backend with ask(), new_chat(), usage(), and terminal chat loop
├── shop.py            # Preprocessor for shop files (PDF, HTML, MD, TXT into plain text shop sheet)
├── check.py           # Regression test: 5 fixed questions against our answer key, PASS or FAIL
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
│   ├── system/
│   │   ├── examples.txt        # Role + 3 example Q&As (default)
│   │   ├── role.txt            # 2-line role definition
│   │   ├── step-by-step.txt    # Role + 4-step answering methodology
│   │   └── shop-assistant.txt  # General shop assistant persona
│   ├── shop/
│   │   ├── faq.md              # Frequently asked questions
│   │   ├── offers.html         # Weekly offers
│   │   ├── phones.txt          # 500 phones in 3 linked tables (added in the tease; see below)
│   │   ├── products.pdf        # Products and prices
│   │   └── returns.txt         # Return policy
│   └── ui-sketch.png
├── .env               # Environment file containing GEMINI_API_KEY (ignored by git)
├── .gitignore         # Git ignore rules for .env, .venv, etc.
├── requirements.txt   # Python dependencies
└── README.md          # Setup and execution guide
```

## What episode 7 adds

**Structured output.** `bot.py` describes the answer with two small Pydantic classes, so Gemini answers in a shape our code can read:

```python
class Item(BaseModel):
    product: str
    price_rupees: int
    quantity: int

class Answer(BaseModel):
    reply: str
    items: list[Item]
```

(In `bot.py` each field also carries a short `Field(description=...)`.) `bot.py` hands `Answer` to Gemini as `response_schema`, with `response_mime_type="application/json"`, and reads the reply back with `Answer.model_validate_json(...)`. The window shows the reply, and under it one line our own code works out: `Total (our code): 1,497 rupees` (price times quantity, added up). `Settings > Structured answers` turns it on or off (on by default; off = plain text, no total line).

**A regression test.** `python check.py` asks Volt 5 fixed questions in a new chat each, adds up Volt's items, and compares each total with the answer we wrote down at the top of `check.py`: PASS or FAIL per line, then `5 of 5 passed`. Run it again after every change.

**Why the files say 949.** In the video the shop changes the charger-with-cable offer from 999 to 949 rupees; the test then fails on that line until we update our answer key. So `prompts/shop/offers.html` and the key in `check.py` both say 949: the project as it stands at the end of the episode.

**Why `phones.txt` is here.** At the end, the shop gets another price list: 500 mobile phones in 3 linked tables (information, pricing, availability, joined by a Product ID; invented prices). With context stuffing the shop sheet grows to about 42,000 tokens, sent with every question. That is the starting point of episode 8, where the phones move into an Excel sheet and Volt fetches only the rows a question needs, with a tool. Delete `phones.txt` (or untick `Settings > Shop files`) if you want the small, cheap shop sheet back.

**How it was built.** Both prompts were given to the agent in Antigravity, model Gemini 3.8 Flash with Thinking effort Medium.

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
  - `Settings > New chat`: Empties the chat history and running summary in `bot.py` and clears the chat area (keeps the chosen character version).
  - `Settings > Reset to defaults`: Reverts all settings (including memory, character toggle, character version, today's date, and shop files toggle) back to starting defaults.
- **Settings & Status Line**: Small grey line under the menu bar displaying active parameters, memory state, character version, date status, and shop status (e.g., `Temperature 1.0 · Top-P 0.95 · Max tokens 2000 · Short-term on, 3 exchanges, 3 in the window. Long-term on, 5 summarised · Character: Volt (examples) · Date: on · Shop: 4 files, 331 tokens`).
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

Five lines, each with the question, Volt's total, our expected total and PASS or FAIL, then `N of 5 passed`. Edit the `CHECKS` list at the top to add your own questions and the totals you expect.

### 7. Backend Functions

- `ask(question, temperature=1.0, top_p=0.95, max_output_tokens=2000, short_term_memory=True, memory_window=6, long_term_memory=True, character=True, character_version="examples", today_date=True, shop_files=True, structured_answers=True)`: Sends system instruction combining today's date line (if enabled), character prompt (if enabled), and shop sheet (if enabled), summary first (if present), up to the last $N$ exchanges from history, then the new question to Gemini. Updates the running summary for exchanges falling outside the window, and returns an `AskResult` with reply text, the structured `items` (when structured answers are on), token usage `(tokens_in, tokens_out)`, and stopped reason.
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
- `get_shop_status(shop_files=True)`: Returns the shop status string (e.g., `Shop: 4 files, 331 tokens` or `Shop: off`).
- `new_chat()`: Empties the in-memory chat history list and clears the running summary.
- `get_summary()`: Returns the current running summary string.
- `get_summarized_count()`: Returns the number of exchanges summarized so far.
- `usage()`: Returns the cumulative totals for the current run: `(tokens_in, tokens_out, cost_in_dollars)`.
