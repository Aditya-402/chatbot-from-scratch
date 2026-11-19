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
DEFAULT_MEMORY_WINDOW = 6
DEFAULT_SHORT_TERM_MEMORY = True
DEFAULT_LONG_TERM_MEMORY = True

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

# History of exchanges: list of (question, reply) tuples
history: list[tuple[str, str]] = []

# Long-term memory running summary of exchanges falling outside memory window
summary: str = ""
_summarized_count: int = 0


def new_chat() -> None:
    """Empties the chat history and clears the summary."""
    global summary, _summarized_count
    history.clear()
    summary = ""
    _summarized_count = 0


def get_history() -> list[tuple[str, str]]:
    """Returns a copy of the chat history so far."""
    return list(history)


def get_summary() -> str:
    """Returns the current running summary."""
    return summary


def get_summarized_count() -> int:
    """Returns the number of exchanges that have been summarized so far."""
    return _summarized_count


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


def _update_summary_with_exchange(past_q: str, past_reply: str) -> None:
    """Asks Gemini to update the running summary with one exchange that fell outside the window."""
    global summary, _total_tokens_in, _total_tokens_out

    if summary:
        prompt = (
            f"Current summary:\n{summary}\n\n"
            f"New exchange to incorporate:\nUser: {past_q}\nBot: {past_reply}\n\n"
            "Please update the summary to include the new exchange. "
            "Keep the summary short, at most 100 words, and keep facts about me such as my name."
        )
    else:
        prompt = (
            f"Exchange to summarize:\nUser: {past_q}\nBot: {past_reply}\n\n"
            "Please write a short summary of this exchange. "
            "Keep the summary short, at most 100 words, and keep facts about me such as my name."
        )

    summary_config = types.GenerateContentConfig(
        temperature=DEFAULT_TEMPERATURE,
        top_p=DEFAULT_TOP_P,
        max_output_tokens=300,
        thinking_config=types.ThinkingConfig(
            thinking_level="MINIMAL",
        ),
    )

    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ],
            config=summary_config,
        )

        new_summary_text = ""
        try:
            new_summary_text = resp.text or ""
        except Exception:
            if resp.candidates:
                c = resp.candidates[0]
                if c.content and c.content.parts:
                    new_summary_text = "".join(
                        p.text for p in c.content.parts if getattr(p, "text", None)
                    )

        if new_summary_text.strip():
            summary = new_summary_text.strip()

        # Count the tokens of the summary updates in the token counter too
        tin = 0
        tout = 0
        if resp.usage_metadata:
            tin = resp.usage_metadata.prompt_token_count or 0
            tout = resp.usage_metadata.candidates_token_count or 0

        _total_tokens_in += tin
        _total_tokens_out += tout
    except Exception:
        pass


def catch_up_summary(
    short_term_memory: bool = DEFAULT_SHORT_TERM_MEMORY,
    memory_window: int = DEFAULT_MEMORY_WINDOW,
    long_term_memory: bool = DEFAULT_LONG_TERM_MEMORY,
) -> None:
    """Summarizes any exchanges that have fallen outside the memory window."""
    global _summarized_count
    if not long_term_memory:
        return

    target_outside = max(
        0, len(history) - (memory_window if short_term_memory else 0)
    )
    while _summarized_count < target_outside:
        past_q, past_a = history[_summarized_count]
        _update_summary_with_exchange(past_q, past_a)
        _summarized_count += 1


def ask(
    question: str,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    short_term_memory: bool = DEFAULT_SHORT_TERM_MEMORY,
    memory_window: int = DEFAULT_MEMORY_WINDOW,
    long_term_memory: bool = DEFAULT_LONG_TERM_MEMORY,
):
    """Sends question to Gemini with short-term & long-term memory and returns reply text and token usage (tokens in, tokens out)."""
    global _total_tokens_in, _total_tokens_out

    contents = []

    # 1. Send the summary first (if long_term_memory is enabled and summary exists)
    if long_term_memory and summary:
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=f"Summary of earlier conversation:\n{summary}"
                    ),
                ],
            )
        )
        contents.append(
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="I understand and will remember this context."
                    ),
                ],
            )
        )

    # 2. Then the last N exchanges word for word
    if short_term_memory and memory_window > 0:
        past_exchanges = history[-memory_window:]
        for past_q, past_reply in past_exchanges:
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=past_q),
                    ],
                )
            )
            contents.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(text=past_reply),
                    ],
                )
            )

    # 3. Then the new question
    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=question),
            ],
        )
    )

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

    # Keep exchange in history (one exchange = one question plus its reply)
    history.append((question, reply_text))

    # When an exchange falls outside the window, update running summary
    if long_term_memory:
        catch_up_summary(
            short_term_memory=short_term_memory,
            memory_window=memory_window,
            long_term_memory=long_term_memory,
        )

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
