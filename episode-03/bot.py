import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client()
MODEL = "gemini-3.1-flash-lite"
DEFAULT_TEMPERATURE = 1.0
DEFAULT_TOP_P = 0.95
DEFAULT_MAX_OUTPUT_TOKENS = 2000

CONFIG = types.GenerateContentConfig(
    temperature=DEFAULT_TEMPERATURE,
    top_p=DEFAULT_TOP_P,
    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
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

    def __new__(cls, reply: str, tokens_in: int, tokens_out: int, finish_reason=None):
        instance = super().__new__(cls, (reply, (tokens_in, tokens_out)))
        instance._finish_reason = finish_reason
        return instance

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

    @property
    def finish_reason(self):
        return self._finish_reason

    @property
    def stopped_max_tokens(self) -> bool:
        if self._finish_reason is None:
            return False
        return "MAX_TOKENS" in str(self._finish_reason).upper()

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


def ask(
    question: str,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
):
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

    config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_output_tokens,
        thinking_config=types.ThinkingConfig(
            thinking_level="MINIMAL",
        ),
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=config,
    )

    reply_text = ""
    try:
        reply_text = response.text or ""
    except Exception:
        if response.candidates:
            c = response.candidates[0]
            if c.content and c.content.parts:
                reply_text = "".join(p.text for p in c.content.parts if getattr(p, "text", None))

    tokens_in = 0
    tokens_out = 0
    if response.usage_metadata:
        tokens_in = response.usage_metadata.prompt_token_count or 0
        tokens_out = response.usage_metadata.candidates_token_count or 0

    finish_reason = None
    if response.candidates and len(response.candidates) > 0:
        finish_reason = getattr(response.candidates[0], "finish_reason", None)

    _total_tokens_in += tokens_in
    _total_tokens_out += tokens_out

    return AskResult(reply_text, tokens_in, tokens_out, finish_reason=finish_reason)


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
