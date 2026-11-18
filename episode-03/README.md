# Chatbot Series - 03 Settings & Desktop Window

A chatbot application powered by the Google GenAI SDK (`gemini-3.1-flash-lite`). It includes a desktop GUI window (`ui.py`) built with Tkinter featuring customizable generation settings (Temperature, Top-P, Max tokens) inspired by Google AI Studio, as well as a terminal interface (`bot.py`), speech bubbles, token tracking, and error handling.

## Project Structure

```text
├── ui.py              # Desktop window (frontend with Tkinter)
├── bot.py             # Chatbot backend with ask(), usage(), and terminal chat loop
├── prompts/           # Prompts and UI sketch
│   ├── 01-api-key.txt
│   ├── 02-terminal-chat.txt
│   ├── 02-window.txt
│   ├── 03-settings.txt
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
  - `Settings > Reset to defaults`: Reverts all settings back to starting defaults.
- **Settings Status Line**: Small grey line under the menu bar always displaying the active parameters (e.g., `Temperature 1.0 · Top-P 0.95 · Max tokens 2000`).
- **Chat Area**: Read-only with selectable and copyable text.
- **Bubbles**: User queries on the left in plum (`#5a3d5c`) and bot replies on the right in ink (`#2b2730`).
- **Reply Metadata Line**: Under each reply, displays tokens in/out, settings used, and `"stopped: max tokens"` when the response was cut short.
- **Token Counter**: Top-right badge showing cumulative tokens; hover to inspect tokens in, tokens out, and cost.
- **Typing & Sending**: Type in the bottom input box and click **Send** or press **Enter**.
- **Error Handling**: Graceful error notifications (e.g. 429 quota exhaustion, 503 unavailability, or internet disconnection) in clay (`#a8441f`).

### 5. Run the Terminal Chat

Run the terminal chat loop:
```bash
python bot.py
```

- Type your question when prompted (`You: `).
- The chatbot replies (`Bot: `) and prompts for the next question using starting default settings.
- Type `exit` or `bye` to end the session.

### 6. Backend Functions

- `ask(question, temperature=1.0, top_p=0.95, max_output_tokens=2000)`: Sends a question to Gemini and returns an `AskResult` with reply text, token usage `(tokens_in, tokens_out)`, and stopped reason.
- `usage()`: Returns the cumulative totals for the current run: `(tokens_in, tokens_out, cost_in_dollars)`.
