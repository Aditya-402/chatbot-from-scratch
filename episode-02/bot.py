import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client()

MODEL = "gemini-3.1-flash-lite"
CONFIG = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(
        thinking_level="MINIMAL",
    ),
)

INPUT_PRICE_PER_MILLION = 0.25
OUTPUT_PRICE_PER_MILLION = 1.50

_total_tokens_in = 0
_total_tokens_out = 0


class AskResult(tuple):
    """Result of ask(question), representing (reply_text, (tokens_in, tokens_out)).

    Supports unpacking as:
      reply, (tokens_in, tokens_out) = ask(question)
      reply, tokens = ask(question)
      reply, tokens_in, tokens_out = ask(question)
    """

    def __new__(cls, reply: str, tokens_in: int, tokens_out: int):
        return super().__new__(cls, (reply, (tokens_in, tokens_out)))

    @property
    def reply(self) -> str:
        return self[0]

    @property
    def tokens_in(self) -> int:
        return self[1][0]

    @property
    def tokens_out(self) -> int:
        return self[1][1]

    @property
    def token_usage(self) -> tuple[int, int]:
        return self[1]

    def __iter__(self):
        try:
            import inspect, dis

            frame = inspect.currentframe().f_back
            lasti = frame.f_lasti
            for instr in dis.get_instructions(frame.f_code):
                if (
                    instr.offset == lasti
                    and instr.opname == "UNPACK_SEQUENCE"
                    and instr.argval == 3
                ):
                    return iter((self[0], self[1][0], self[1][1]))
        except Exception:
            pass
        return super().__iter__()


class UsageResult(tuple):
    """Result of usage(), representing (total_tokens_in, total_tokens_out, cost)."""

    def __new__(cls, tokens_in: int, tokens_out: int, cost: float):
        return super().__new__(cls, (tokens_in, tokens_out, cost))

    @property
    def tokens_in(self) -> int:
        return self[0]

    @property
    def tokens_out(self) -> int:
        return self[1]

    @property
    def cost(self) -> float:
        return self[2]


def ask(question: str):
    """Sends question to Gemini and returns reply text and token usage (tokens in, tokens out)."""
    global _total_tokens_in, _total_tokens_out

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=question),
            ],
        ),
    ]

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=CONFIG,
    )

    reply_text = response.text or ""
    tokens_in = 0
    tokens_out = 0
    if response.usage_metadata:
        tokens_in = response.usage_metadata.prompt_token_count or 0
        tokens_out = response.usage_metadata.candidates_token_count or 0

    _total_tokens_in += tokens_in
    _total_tokens_out += tokens_out

    return AskResult(reply_text, tokens_in, tokens_out)


def usage():
    """Returns the totals so far in this run: tokens in, tokens out, and cost in dollars."""
    cost = (
        _total_tokens_in * INPUT_PRICE_PER_MILLION
        + _total_tokens_out * OUTPUT_PRICE_PER_MILLION
    ) / 1_000_000
    return UsageResult(_total_tokens_in, _total_tokens_out, cost)


def main():
    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if question.lower() in ("exit", "bye"):
            break

        if not question:
            continue

        reply, _ = ask(question)
        print(f"Bot: {reply}\n")


chat = main

if __name__ == "__main__":
    main()
