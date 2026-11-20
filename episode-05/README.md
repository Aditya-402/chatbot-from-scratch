# Chatbot Series - 05 Character & Prompt Styles

A chatbot application powered by the Google GenAI SDK (`gemini-3.1-flash-lite`). It includes a desktop GUI window (`ui.py`) built with Tkinter featuring customizable generation settings (Temperature, Top-P, Max tokens), short-term memory (sliding exchange window), long-term memory (running summary of older exchanges), selectable and editable character prompt styles (`examples`, `role`, `step-by-step`, `shop-assistant`) loaded from `prompts/system/`, as well as a terminal interface (`bot.py`), speech bubbles, token tracking, and error handling.

## Project Structure

```text
├── ui.py              # Desktop window (frontend with Tkinter)
├── bot.py             # Chatbot backend with ask(), new_chat(), usage(), and terminal chat loop
├── prompts/           # Prompts and UI sketch
│   ├── 01-api-key.txt
│   ├── 02-terminal-chat.txt
│   ├── 02-window.txt
│   ├── 03-settings.txt
│   ├── 04-memory.txt
│   ├── 04-summary.txt
│   ├── 05-character.txt
│   ├── 05-styles.txt
│   ├── system/
│   │   ├── examples.txt        # Role + 3 example Q&As (default)
│   │   ├── role.txt            # 2-line role definition
│   │   ├── step-by-step.txt    # Role + 4-step answering methodology
│   │   └── shop-assistant.txt  # General shop assistant persona
│   └── ui-sketch.png
├── .env               # Environment file containing GEMINI_API_KEY (ignored by git)
├── .gitignore         # Git ignore rules for .env, .venv, etc.
├── requirements.txt   # Python dependencies
└── README.md          # Setup and execution guide
```

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
  - `Settings > New chat`: Empties the chat history and running summary in `bot.py` and clears the chat area (keeps the chosen character version).
  - `Settings > Reset to defaults`: Reverts all settings (including memory, character toggle, and character version) back to starting defaults.
- **Settings & Status Line**: Small grey line under the menu bar displaying active parameters, memory state, and character version (e.g., `Temperature 1.0 · Top-P 0.95 · Max tokens 2000 · Short-term on, 3 exchanges, 3 in the window. Long-term on, 5 summarised · Character: Volt (examples)`).
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
- The chatbot replies (`Bot: `) with the Volt character (`examples` style by default), and retains both short-term memory (last 6 exchanges) and long-term memory (running summary of exchanges falling outside the window) across questions using default settings.
- Type `exit` or `bye` to end the session.

### 6. Backend Functions

- `ask(question, temperature=1.0, top_p=0.95, max_output_tokens=2000, short_term_memory=True, memory_window=6, long_term_memory=True, character=True, character_version="examples")`: Sends system instruction for the chosen version (if character is enabled), summary first (if present), up to the last $N$ exchanges from history, then the new question to Gemini. Updates the running summary for exchanges falling outside the window, and returns an `AskResult` with reply text, token usage `(tokens_in, tokens_out)`, and stopped reason.
- `get_character_versions()`: Returns a list of character versions available in `prompts/system/`.
- `load_system_prompt(version="examples")`: Reads and returns the content of `prompts/system/<version>.txt`.
- `save_system_prompt(version, text)`: Saves edited text to `prompts/system/<version>.txt`.
- `get_character_status(character=True, version="examples")`: Returns the status string (e.g., `Character: Volt (examples)` or `Character: off`).
- `new_chat()`: Empties the in-memory chat history list and clears the running summary.
- `get_summary()`: Returns the current running summary string.
- `get_summarized_count()`: Returns the number of exchanges summarized so far.
- `usage()`: Returns the cumulative totals for the current run: `(tokens_in, tokens_out, cost_in_dollars)`.
