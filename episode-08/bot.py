import os
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from shop import get_shop_sheet, count_shop_files, load_shop_files, SHOP_DIR
from tools import find_phone

load_dotenv()

client = genai.Client()
MODEL = "gemini-3.1-flash-lite"
DEFAULT_TEMPERATURE = 1.0
DEFAULT_TOP_P = 0.95
DEFAULT_MAX_OUTPUT_TOKENS = 2000
DEFAULT_MEMORY_WINDOW = 6
DEFAULT_SHORT_TERM_MEMORY = True
DEFAULT_LONG_TERM_MEMORY = True
DEFAULT_CHARACTER = True
DEFAULT_CHARACTER_VERSION = "examples"
CHARACTER_NAME = "Volt"
DEFAULT_TODAY_DATE = True
DEFAULT_DATE = True
DEFAULT_SHOP_FILES = True
DEFAULT_STRUCTURED_ANSWERS = True
DEFAULT_STRUCTURED = True
DEFAULT_PHONE_LOOKUP = True

FIND_PHONE_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="find_phone",
            description="look up a phone's price and stock by its model name",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "model": types.Schema(
                        type=types.Type.STRING,
                        description="Phone model name to look up",
                    ),
                },
                required=["model"],
            ),
        )
    ]
)

SYSTEM_PROMPTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "prompts", "system"
)
SYSTEM_PROMPT_PATH = os.path.join(SYSTEM_PROMPTS_DIR, "shop-assistant.txt")


def get_character_versions() -> list[str]:
    """Returns a sorted list of available character versions found in prompts/system/."""
    if not os.path.isdir(SYSTEM_PROMPTS_DIR):
        return [DEFAULT_CHARACTER_VERSION]
    versions = []
    for fname in os.listdir(SYSTEM_PROMPTS_DIR):
        if fname.endswith(".txt"):
            versions.append(fname[:-4])
    versions.sort()
    return versions if versions else [DEFAULT_CHARACTER_VERSION]


def get_system_prompt_path(version: str = DEFAULT_CHARACTER_VERSION) -> str:
    """Returns the file path for a given character version or filename."""
    if os.path.isabs(version):
        return version
    if not version.endswith(".txt"):
        version = f"{version}.txt"
    return os.path.join(SYSTEM_PROMPTS_DIR, version)


def load_system_prompt(version: str = DEFAULT_CHARACTER_VERSION) -> str:
    """Loads the character system prompt from file for the given version or path."""
    if os.path.isfile(version):
        path = version
    else:
        path = get_system_prompt_path(version)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def save_system_prompt(version: str, text: str) -> str:
    """Saves the system prompt text to the specified version file."""
    os.makedirs(SYSTEM_PROMPTS_DIR, exist_ok=True)
    path = get_system_prompt_path(version)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


CONFIG = types.GenerateContentConfig(
    system_instruction=load_system_prompt(DEFAULT_CHARACTER_VERSION),
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


class Item(BaseModel):
    product: str = Field(description="Name of the product")
    price_rupees: int = Field(description="Price per item in rupees from the shop sheet as a plain whole number")
    quantity: int = Field(description="Quantity asked for as a whole number")


class Answer(BaseModel):
    reply: str = Field(description="Volt's conversational reply to the customer")
    items: list[Item] = Field(
        default_factory=list,
        description="List of each product the question asks about, with its price from the shop sheet and the quantity asked. When the question has no price in the shop sheet, items is empty.",
    )


class AskResult(tuple):
    """Result of ask(question), representing (reply_text, (tokens_in, tokens_out)).

    Supports unpacking as:
      reply, (tokens_in, tokens_out) = ask(question)
      reply, tokens = ask(question)
      reply, tokens_in, tokens_out = ask(question)
    """

    def __new__(
        cls,
        reply: str,
        tokens_in: int,
        tokens_out: int,
        finish_reason=None,
        answer: Answer | None = None,
        items: list[Item] | None = None,
        tool_calls: list[dict] | None = None,
    ):
        instance = super().__new__(cls, (reply, (tokens_in, tokens_out)))
        instance._finish_reason = finish_reason
        instance._answer = answer
        instance._items = items if items is not None else (answer.items if answer else [])
        instance._tool_calls = tool_calls or []
        return instance

    @property
    def reply(self) -> str:
        return self[0]

    @property
    def answer(self) -> Answer | None:
        return self._answer

    @property
    def items(self) -> list[Item]:
        return self._items or []

    @property
    def tool_calls(self) -> list[dict]:
        return self._tool_calls

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


def get_character_status(
    character: bool = True, version: str = DEFAULT_CHARACTER_VERSION
) -> str:
    """Returns the character display string for the status line."""
    if not character:
        return "Character: off"
    return f"Character: {CHARACTER_NAME} ({version})"


def get_date_status(today_date: bool = DEFAULT_TODAY_DATE) -> str:
    """Returns the date display string for the status line."""
    return "Date: on" if today_date else "Date: off"


def get_today_date_line(now: datetime | None = None) -> str:
    """Returns 'Today is <weekday, day month year>, <time>.' for the current moment."""
    if now is None:
        now = datetime.now()
    return f"Today is {now.strftime('%A')}, {now.day} {now.strftime('%B %Y')}, {now.strftime('%H:%M')}."


_shop_sheet: str = ""
_shop_files_count: int = 0
_shop_tokens_count: int = 0


def reload_shop_files() -> tuple[str, int, int]:
    """Reloads shop files from prompts/shop/, rebuilds shop sheet, and updates counts."""
    global _shop_sheet, _shop_files_count, _shop_tokens_count
    _shop_sheet = get_shop_sheet()
    _shop_files_count = count_shop_files()
    try:
        res = client.models.count_tokens(model=MODEL, contents=_shop_sheet)
        _shop_tokens_count = res.total_tokens or 0
    except Exception:
        _shop_tokens_count = max(1, len(_shop_sheet) // 4) if _shop_sheet else 0
    return _shop_sheet, _shop_files_count, _shop_tokens_count


def get_current_shop_sheet() -> str:
    """Returns the current shop sheet, loading it if not yet cached."""
    global _shop_sheet
    if not _shop_sheet:
        reload_shop_files()
    return _shop_sheet


def get_shop_files_count() -> int:
    """Returns the number of shop files loaded."""
    global _shop_files_count
    if not _shop_sheet:
        reload_shop_files()
    return _shop_files_count


def get_shop_tokens_count() -> int:
    """Returns the token count for the shop sheet."""
    global _shop_tokens_count
    if not _shop_sheet:
        reload_shop_files()
    return _shop_tokens_count


def get_shop_status(shop_files: bool = True) -> str:
    """Returns the shop files display string for the status line."""
    if not shop_files:
        return "Shop: off"
    count = get_shop_files_count()
    tokens = get_shop_tokens_count()
    files_label = "file" if count == 1 else "files"
    return f"Shop: {count} {files_label}, {tokens} tokens"


def get_phone_lookup_status(phone_lookup: bool = True) -> str:
    """Returns the phone lookup tool display string for the status line."""
    return "Phone lookup: on" if phone_lookup else "Phone lookup: off"


def ask(
    question: str,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    short_term_memory: bool = DEFAULT_SHORT_TERM_MEMORY,
    memory_window: int = DEFAULT_MEMORY_WINDOW,
    long_term_memory: bool = DEFAULT_LONG_TERM_MEMORY,
    character: bool | str = DEFAULT_CHARACTER,
    character_version: str = DEFAULT_CHARACTER_VERSION,
    today_date: bool = DEFAULT_TODAY_DATE,
    shop_files: bool = DEFAULT_SHOP_FILES,
    structured_answers: bool = DEFAULT_STRUCTURED_ANSWERS,
    phone_lookup: bool = DEFAULT_PHONE_LOOKUP,
    **kwargs,
):
    """Sends question to Gemini with character, short-term & long-term memory, today's date, shop sheet, optional phone lookup tool, and optional structured output, and returns reply text and token usage."""
    global _total_tokens_in, _total_tokens_out

    if "date" in kwargs:
        today_date = kwargs["date"]
    if "shop" in kwargs:
        shop_files = kwargs["shop"]
    if "structured" in kwargs:
        structured_answers = kwargs["structured"]
    if "structured_answers" in kwargs:
        structured_answers = kwargs["structured_answers"]
    if "phone_lookup" in kwargs:
        phone_lookup = kwargs["phone_lookup"]

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

    char_prompt = ""
    if character:
        if isinstance(character, str):
            char_prompt = character.strip()
        else:
            char_prompt = load_system_prompt(character_version).strip()

    date_line = ""
    if today_date:
        date_line = get_today_date_line()

    shop_sheet = ""
    if shop_files:
        shop_sheet = get_current_shop_sheet().strip()

    instruction_parts = []
    if date_line and char_prompt:
        instruction_parts.append(f"{date_line}\n{char_prompt}")
    elif date_line:
        instruction_parts.append(date_line)
    elif char_prompt:
        instruction_parts.append(char_prompt)

    if shop_sheet:
        instruction_parts.append(shop_sheet)

    if phone_lookup:
        instruction_parts.append(
            "You have a tool find_phone to look up a phone's price and stock by its model name. "
            "ONLY call find_phone when the customer asks about a smartphone / mobile phone. "
            "Do NOT call find_phone for chargers, cables, earbuds, phone stands, or other accessories—those are in the shop sheet above. "
            "When find_phone returns no rows for a phone, say we don't sell that phone. Never invent a phone price."
        )

    if structured_answers:
        instruction_parts.append(
            "When answering, items lists each product the question asks about, with its price from the shop sheet or from find_phone and the quantity asked. When the question has no price in the shop sheet or find_phone, items is empty."
        )

    system_instruction = "\n\n".join(instruction_parts) if instruction_parts else None

    config_kwargs = dict(
        system_instruction=system_instruction,
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_output_tokens,
        thinking_config=types.ThinkingConfig(
            thinking_level="MINIMAL",
        ),
    )
    if phone_lookup:
        config_kwargs["tools"] = [FIND_PHONE_TOOL]
    if structured_answers:
        config_kwargs["response_mime_type"] = "application/json"
        config_kwargs["response_schema"] = Answer

    config = types.GenerateContentConfig(**config_kwargs)

    tokens_in = 0
    tokens_out = 0
    tool_calls_log: list[dict] = []
    seen_calls: set[tuple[str, str]] = set()
    response = None

    for _ in range(4):
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=config,
        )

        if response.usage_metadata:
            tokens_in += response.usage_metadata.prompt_token_count or 0
            tokens_out += response.usage_metadata.candidates_token_count or 0

        function_calls = getattr(response, "function_calls", None) or []
        if not function_calls:
            break

        # If every requested call was already executed, stop tool calling and ask for final answer
        call_keys = [
            (fc.name, str((dict(fc.args) if fc.args else {}).get("model", "")).strip().lower())
            for fc in function_calls
        ]
        if all(k in seen_calls for k in call_keys):
            no_tools_config = types.GenerateContentConfig(
                **{k: v for k, v in config_kwargs.items() if k != "tools"}
            )
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=no_tools_config,
            )
            if response.usage_metadata:
                tokens_in += response.usage_metadata.prompt_token_count or 0
                tokens_out += response.usage_metadata.candidates_token_count or 0
            break

        if response.candidates and response.candidates[0].content:
            contents.append(response.candidates[0].content)

        response_parts = []
        for fc in function_calls:
            fc_name = fc.name
            fc_args = dict(fc.args) if fc.args else {}
            if fc_name == "find_phone":
                model_arg = str(fc_args.get("model", ""))
                seen_calls.add((fc_name, model_arg.strip().lower()))
                rows = find_phone(model_arg)
                tool_calls_log.append(
                    {
                        "name": fc_name,
                        "args": fc_args,
                        "row_count": len(rows),
                    }
                )
                response_parts.append(
                    types.Part.from_function_response(
                        name=fc_name,
                        response={"rows": rows},
                    )
                )
            else:
                response_parts.append(
                    types.Part.from_function_response(
                        name=fc_name,
                        response={"error": f"Unknown tool: {fc_name}"},
                    )
                )

        contents.append(types.Content(role="user", parts=response_parts))
    else:
        # Loop ended with pending function calls; ask once more without tools
        no_tools_config = types.GenerateContentConfig(
            **{k: v for k, v in config_kwargs.items() if k != "tools"}
        )
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=no_tools_config,
        )
        if response.usage_metadata:
            tokens_in += response.usage_metadata.prompt_token_count or 0
            tokens_out += response.usage_metadata.candidates_token_count or 0

    raw_text = ""
    try:
        raw_text = response.text or ""
    except Exception:
        if response and response.candidates:
            c = response.candidates[0]
            if c.content and c.content.parts:
                raw_text = "".join(p.text for p in c.content.parts if getattr(p, "text", None))

    reply_text = raw_text
    answer_obj = None
    items: list[Item] = []

    if structured_answers and raw_text:
        try:
            clean_text = raw_text.strip()
            if clean_text.startswith("```"):
                lines = clean_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_text = "\n".join(lines).strip()
            answer_obj = Answer.model_validate_json(clean_text)
            reply_text = answer_obj.reply
            items = answer_obj.items or []
        except Exception:
            pass

    finish_reason = None
    if response and response.candidates and len(response.candidates) > 0:
        finish_reason = getattr(response.candidates[0], "finish_reason", None)

    _total_tokens_in += tokens_in
    _total_tokens_out += tokens_out

    # Keep exchange in history (one exchange = one question plus its reply)
    # The memory keeps the reply text only.
    history.append((question, reply_text))

    # When an exchange falls outside the window, update running summary
    if long_term_memory:
        catch_up_summary(
            short_term_memory=short_term_memory,
            memory_window=memory_window,
            long_term_memory=long_term_memory,
        )

    return AskResult(
        reply_text,
        tokens_in,
        tokens_out,
        finish_reason=finish_reason,
        answer=answer_obj,
        items=items,
        tool_calls=tool_calls_log,
    )


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

        res = ask(question)
        print(f"Bot: {res.reply}\n")
        if res.items:
            total = sum(item.price_rupees * item.quantity for item in res.items)
            print(f"Total (our code): {total:,} rupees\n")


chat = main

if __name__ == "__main__":
    main()
