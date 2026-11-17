# Chatbot Series - 01 API Key Setup

A simple chatbot script using the Google GenAI SDK (`gemini-3.1-flash-lite`), configured to securely read the Gemini API key from environment variables.

## Project Structure

```text
├── bot.py             # Chatbot script
├── .env               # Environment file containing GEMINI_API_KEY (ignored by git)
├── .gitignore         # Git ignore rules for .env, .venv, etc.
├── requirements.txt   # Python dependencies
└── README.md          # Setup and execution guide
```

## Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher installed.

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the required libraries listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory (if not already present) and add your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Run the Chatbot

Execute the bot script:
```bash
python bot.py
```

