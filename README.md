# Chatbot from Scratch

The code of the **Chatbot from Scratch** series by [Learn AI by Building](https://learnaibybuilding.in/series/chatbots/):
a chatbot on Google's Gemini, built in Python one episode at a time by prompting a coding agent.

Each folder is the complete project as it stands **at the end of that episode**, so you can start from any episode.

| Folder | Episode | What it adds | Download |
|---|---|---|---|
| [episode-01](episode-01) | How do I talk to Gemini from my own Python code? | `bot.py` asks Gemini one question; the key lives in `.env` | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-01) |
| [episode-02](episode-02) | How do I give my chatbot its own window? | a terminal chat, then `ui.py`: a window (frontend) that talks to `bot.py` (backend) | [zip](https://github.com/Aditya-402/chatbot-from-scratch/releases/tag/episode-02) |

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
