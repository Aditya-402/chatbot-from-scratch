# Chatbot from Scratch

The code of the **Chatbot from Scratch** series by [Learn AI by Building](https://learnaibybuilding.in/series/chatbots/):
a chatbot on Google's Gemini, built in Python one episode at a time by prompting a coding agent.

Each folder is the complete project as it stands **at the end of that episode**, so you can start from any episode.

| Folder | Episode | What it adds | Download |
|---|---|---|---|
| [episode-01](episode-01) | How do I talk to Gemini from my own Python code? | `bot.py` asks Gemini one question; the key lives in `.env` | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-01) |
| [episode-02](episode-02) | How do I give my chatbot its own window? | a terminal chat, then `ui.py`: a window (frontend) that talks to `bot.py` (backend) | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-02) |
| [episode-03](episode-03) | Why does the same question give different answers? | a Settings menu in the window: temperature, top-P, max tokens (top-K fixed at 64) | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-03) |
| [episode-04](episode-04) | Why does my chatbot forget what I just told it? | a short-term memory (last N exchanges, window 0-15) and a long-term memory (one running summary), both switchable; New chat | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-04) |
| [episode-05](episode-05) | How do I make my chatbot behave like a shop assistant? | a character: system prompts in prompts/system/ (role, step by step, examples), switched and edited in Settings, with an on/off tick | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-05) |
| [episode-06](episode-06) | How do I teach my chatbot about my own shop? | today's date and a shop sheet: shop.py turns a PDF, a web page, Markdown and text in prompts/shop/ into plain text sent with every call (context stuffing), with Reload and Show shop sheet in Settings | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-06) |
| [episode-07](episode-07) | How do I get an answer my code can use, not just read? | structured answers: Gemini fills a Pydantic shape (reply + items) and our code adds up the total; `check.py`, a regression test against our own answer key | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-07) |
| [episode-08](episode-08) | How does my chatbot look things up in my own data? | the first tool: `find_phone` in `tools.py` reads the 500-phone workbook `data/phones.xlsx`; our own code runs the call and sends the rows back | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-08) |
| [episode-09](episode-09) | How does my chatbot answer a question that needs several look-ups? | the first agent: `list_phones` and `check_delivery` join `find_phone`; our own code runs them in a loop with a step cap; `agent.txt` (Plan, Execute, Evaluate, Iterate); structured answers shaped once at the end | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-09) |

## Run an episode

1. Download the episode's zip (or clone this repository) and open its folder.
2. Make a virtual environment and install the libraries:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a file `.env` in the folder with your own key: `GEMINI_API_KEY=your-key-here`.
   Get a key in Google AI Studio. Never share it and never commit it: `.gitignore` keeps `.env` out of git.
4. Run `python bot.py` (from episode 2 on, `python ui.py` opens the window).

Every prompt we gave the agent is in each episode's `prompts/` folder.
