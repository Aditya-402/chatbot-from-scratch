import queue
import threading
import tkinter as tk
from bot import (
    ask,
    usage,
    new_chat,
    history,
    get_summary,
    get_summarized_count,
    catch_up_summary,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MEMORY_WINDOW,
    DEFAULT_SHORT_TERM_MEMORY,
    DEFAULT_LONG_TERM_MEMORY,
    DEFAULT_CHARACTER,
    DEFAULT_CHARACTER_VERSION,
    DEFAULT_TODAY_DATE,
    DEFAULT_SHOP_FILES,
    DEFAULT_STRUCTURED_ANSWERS,
    DEFAULT_PHONE_LOOKUP,
    DEFAULT_STEP_CAP,
    CHARACTER_NAME,
    Item,
    Answer,
    get_character_versions,
    load_system_prompt,
    save_system_prompt,
    get_character_status,
    get_date_status,
    get_shop_status,
    get_phone_lookup_status,
    get_step_cap_status,
    get_current_shop_sheet,
    reload_shop_files,
)

# Learn AI by Building colour palette
COLOR_BG = "#faf6ee"  # cream (window background)
COLOR_CHAT_BG = "#ffffff"  # white (chat area)
COLOR_USER = "#5a3d5c"  # plum (user questions)
COLOR_BOT = "#2b2730"  # ink (bot replies)
COLOR_TOKEN = "#6a626e"  # grey (token line)
COLOR_ERROR = "#a8441f"  # clay (error messages)
COLOR_BORDER = "#2b2730"  # ink outline

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 8)
FONT_INPUT = ("Segoe UI", 11)


def format_error_message(err: Exception) -> str:
    """Translates exceptions into short plain user-friendly messages."""
    err_str = str(err)
    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
        return "Too many requests for the free tier. Wait a minute and try again."
    if "503" in err_str or "UNAVAILABLE" in err_str:
        return "Gemini is busy right now. Try again in a moment."
    err_lower = err_str.lower()
    if any(
        k in err_lower
        for k in [
            "getaddrinfo failed",
            "connecterror",
            "connection refused",
            "network",
            "no internet",
            "gaierror",
            "name resolution",
            "failed to establish a new connection",
        ]
    ):
        return "No internet connection."
    return f"Error: {err_str}" if len(err_str) < 100 else "Something went wrong. Please try again."


class TokenCounterBadge(tk.Frame):
    """Google AI Studio style token counter badge with hover details."""

    def __init__(self, parent):
        super().__init__(
            parent,
            bg=COLOR_CHAT_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
        )
        self.label = tk.Label(
            self,
            text="0 tokens",
            font=FONT_MAIN,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            padx=10,
            pady=3,
            cursor="hand2",
        )
        self.label.pack()
        self.tip_window = None

        self.label.bind("<Enter>", self.show_tooltip)
        self.label.bind("<Leave>", self.hide_tooltip)
        self.bind("<Enter>", self.show_tooltip)
        self.bind("<Leave>", self.hide_tooltip)

    def refresh(self):
        tin, tout, _ = usage()
        total = tin + tout
        self.label.config(text=f"{total:,} tokens")

    def show_tooltip(self, event=None):
        if self.tip_window:
            return
        tin, tout, cost = usage()
        cost_str = f"${cost:.6f}" if cost > 0 else "$0.00"
        tip_text = (
            f"Tokens in: {tin:,}\n"
            f"Tokens out: {tout:,}\n"
            f"Cost so far: {cost_str}"
        )

        x = self.winfo_rootx() - 15
        y = self.winfo_rooty() + self.winfo_height() + 5

        self.tip_window = tk.Toplevel(self)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")

        tip_frame = tk.Frame(
            self.tip_window,
            bg=COLOR_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
        )
        tip_frame.pack()

        tip_label = tk.Label(
            tip_frame,
            text=tip_text,
            font=FONT_SMALL,
            bg=COLOR_BG,
            fg=COLOR_BOT,
            padx=8,
            pady=4,
            justify="left",
        )
        tip_label.pack()

    def hide_tooltip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


def create_bubble_canvas(parent, text: str, is_user: bool, max_width: int = 440) -> tk.Canvas:
    """Draws a speech bubble on a Canvas with selectable read-only text."""
    dummy = tk.Label(parent, text=text, font=FONT_MAIN, wraplength=max_width - 32, justify="left")
    dummy.update_idletasks()
    text_w = max(dummy.winfo_reqwidth(), 60)
    text_h = max(dummy.winfo_reqheight(), 20)
    dummy.destroy()

    pad_x = 14
    pad_y = 10
    tail_h = 10
    bubble_w = text_w + (pad_x * 2)
    bubble_h = text_h + (pad_y * 2)

    canvas_w = bubble_w + 10
    canvas_h = bubble_h + tail_h + 8

    cv = tk.Canvas(
        parent,
        width=canvas_w,
        height=canvas_h,
        bg=COLOR_CHAT_BG,
        highlightthickness=0,
        bd=0,
    )

    x1, y1 = 4, 4
    x2, y2 = x1 + bubble_w, y1 + bubble_h
    r = 12

    # Speech tail points matching the sketch
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + 36, y2,
        x1 + 12, y2 + tail_h,
        x1 + 22, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]

    # Draw rounded bubble outline
    cv.create_polygon(
        points,
        smooth=True,
        fill=COLOR_CHAT_BG,
        outline=COLOR_BORDER,
        width=2,
    )

    # Embedded selectable text inside the bubble
    txt_widget = tk.Text(
        cv,
        font=FONT_MAIN,
        bg=COLOR_CHAT_BG,
        fg=COLOR_USER if is_user else COLOR_BOT,
        bd=0,
        highlightthickness=0,
        wrap="word",
        cursor="xterm",
    )
    txt_widget.insert("1.0", text)

    # Block editing while permitting selection & copying
    def block_keys(event):
        if event.state & 4 and event.keysym.lower() in ("c", "a"):
            return None
        if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"):
            return None
        return "break"

    txt_widget.bind("<KeyPress>", block_keys)
    txt_widget.bind("<<Paste>>", lambda e: "break")
    txt_widget.bind("<<Cut>>", lambda e: "break")

    # Right-click copy context menu
    def show_popup(event):
        menu = tk.Menu(txt_widget, tearoff=0)
        try:
            sel = txt_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            sel = text

        def copy_text():
            parent.clipboard_clear()
            parent.clipboard_append(sel)

        menu.add_command(label="Copy", command=copy_text)
        menu.tk_popup(event.x_root, event.y_root)

    txt_widget.bind("<Button-3>", show_popup)
    cv.bind("<Button-3>", show_popup)

    cv.create_window(
        x1 + pad_x,
        y1 + pad_y,
        window=txt_widget,
        anchor="nw",
        width=text_w + 4,
        height=text_h + 4,
    )
    return cv


class SliderDialog(tk.Toplevel):
    """Dialog showing a slider with current value, OK and Cancel buttons."""

    def __init__(
        self,
        parent,
        title: str,
        current_val: float,
        from_: float,
        to: float,
        resolution: float,
        is_int: bool = False,
    ):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.transient(parent)

        self.result = None
        self.is_int = is_int
        self.resolution = resolution

        def format_val(val: float) -> str:
            if self.is_int:
                return str(int(round(val)))
            if self.resolution == 0.1:
                return f"{val:.1f}"
            return f"{round(val, 2)}"

        content_frame = tk.Frame(self, bg=COLOR_BG, padx=24, pady=18)
        content_frame.pack(fill="both", expand=True)

        self.value_label = tk.Label(
            content_frame,
            text=f"Current value: {format_val(current_val)}",
            font=FONT_MAIN,
            bg=COLOR_BG,
            fg=COLOR_BOT,
        )
        self.value_label.pack(anchor="w", pady=(0, 10))

        def on_slider_move(v):
            self.value_label.config(text=f"Current value: {format_val(float(v))}")

        self.scale = tk.Scale(
            content_frame,
            from_=from_,
            to=to,
            resolution=resolution,
            orient="horizontal",
            length=260,
            bg=COLOR_BG,
            fg=COLOR_BOT,
            highlightthickness=0,
            troughcolor=COLOR_CHAT_BG,
            activebackground=COLOR_USER,
            command=on_slider_move,
        )
        self.scale.set(current_val)
        self.scale.pack(fill="x", pady=(0, 18))

        btn_frame = tk.Frame(content_frame, bg=COLOR_BG)
        btn_frame.pack(fill="x")

        self.cancel_button = tk.Button(
            btn_frame,
            text="Cancel",
            font=FONT_MAIN,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            activebackground="#e5dfd5",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
            padx=16,
            pady=4,
            cursor="hand2",
            command=self.on_cancel,
        )
        self.cancel_button.pack(side="right", padx=(8, 0))

        self.ok_button = tk.Button(
            btn_frame,
            text="OK",
            font=FONT_BOLD,
            bg=COLOR_USER,
            fg="#ffffff",
            activebackground="#452e47",
            activeforeground="#ffffff",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=4,
            cursor="hand2",
            command=self.on_ok,
        )
        self.ok_button.pack(side="right")

        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.on_cancel())

        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = px + max((pw - w) // 2, 0)
        y = py + max((ph - h) // 2, 0)
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.grab_set()

    def on_ok(self):
        val = self.scale.get()
        if self.is_int:
            self.result = int(round(val))
        elif self.resolution == 0.1:
            self.result = round(float(val), 1)
        else:
            self.result = round(float(val), 2)
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class MemoryWindowDialog(tk.Toplevel):
    """Dialog for choosing memory window from 0, 3, 6, 9, 12, or 15 exchanges."""

    CHOICES = [0, 3, 6, 9, 12, 15]

    def __init__(self, parent, current_val: int = DEFAULT_MEMORY_WINDOW):
        super().__init__(parent)
        self.parent = parent
        self.title("Memory window")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.transient(parent)

        if current_val not in self.CHOICES:
            current_val = min(self.CHOICES, key=lambda x: abs(x - current_val))

        self.result = None
        self.selected_val = current_val

        content_frame = tk.Frame(self, bg=COLOR_BG, padx=24, pady=18)
        content_frame.pack(fill="both", expand=True)

        self.value_label = tk.Label(
            content_frame,
            text=f"Current value: {current_val} exchanges",
            font=FONT_MAIN,
            bg=COLOR_BG,
            fg=COLOR_BOT,
        )
        self.value_label.pack(anchor="w", pady=(0, 10))

        def update_val(val: int):
            self.selected_val = val
            self.value_label.config(text=f"Current value: {val} exchanges")
            if hasattr(self, "choice_var") and self.choice_var.get() != val:
                self.choice_var.set(val)
            if hasattr(self, "scale") and int(self.scale.get()) != val:
                self.scale.set(val)

        def on_slider_move(v):
            val = int(round(float(v)))
            if val in self.CHOICES:
                update_val(val)

        self.scale = tk.Scale(
            content_frame,
            from_=0,
            to=15,
            resolution=3,
            orient="horizontal",
            length=260,
            bg=COLOR_BG,
            fg=COLOR_BOT,
            highlightthickness=0,
            troughcolor=COLOR_CHAT_BG,
            activebackground=COLOR_USER,
            command=on_slider_move,
        )
        self.scale.set(current_val)
        self.scale.pack(fill="x", pady=(0, 14))

        self.choice_var = tk.IntVar(value=current_val)
        choices_frame = tk.Frame(content_frame, bg=COLOR_BG)
        choices_frame.pack(fill="x", pady=(0, 18))

        row1 = tk.Frame(choices_frame, bg=COLOR_BG)
        row1.pack(fill="x", pady=2)
        row2 = tk.Frame(choices_frame, bg=COLOR_BG)
        row2.pack(fill="x", pady=2)

        for i, c in enumerate(self.CHOICES):
            target_row = row1 if i < 3 else row2
            rb = tk.Radiobutton(
                target_row,
                text=f"{c} exchanges",
                value=c,
                variable=self.choice_var,
                command=lambda val=c: update_val(val),
                font=FONT_MAIN,
                bg=COLOR_BG,
                fg=COLOR_BOT,
                activebackground=COLOR_BG,
                selectcolor=COLOR_CHAT_BG,
                cursor="hand2",
            )
            rb.pack(side="left", expand=True, anchor="w", padx=4)

        btn_frame = tk.Frame(content_frame, bg=COLOR_BG)
        btn_frame.pack(fill="x")

        self.cancel_button = tk.Button(
            btn_frame,
            text="Cancel",
            font=FONT_MAIN,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            activebackground="#e5dfd5",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
            padx=16,
            pady=4,
            cursor="hand2",
            command=self.on_cancel,
        )
        self.cancel_button.pack(side="right", padx=(8, 0))

        self.ok_button = tk.Button(
            btn_frame,
            text="OK",
            font=FONT_BOLD,
            bg=COLOR_USER,
            fg="#ffffff",
            activebackground="#452e47",
            activeforeground="#ffffff",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=4,
            cursor="hand2",
            command=self.on_ok,
        )
        self.ok_button.pack(side="right")

        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.on_cancel())

        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = px + max((pw - w) // 2, 0)
        y = py + max((ph - h) // 2, 0)
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.grab_set()

    def on_ok(self):
        self.result = int(self.selected_val)
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class MemorySummaryDialog(tk.Toplevel):
    """Small window showing the current long-term memory summary."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Memory summary")
        self.configure(bg=COLOR_BG)
        self.resizable(True, True)
        self.transient(parent)

        content_frame = tk.Frame(self, bg=COLOR_BG, padx=20, pady=16)
        content_frame.pack(fill="both", expand=True)

        header_label = tk.Label(
            content_frame,
            text="Current memory summary:",
            font=FONT_BOLD,
            bg=COLOR_BG,
            fg=COLOR_BOT,
        )
        header_label.pack(anchor="w", pady=(0, 8))

        text_border = tk.Frame(
            content_frame,
            bg=COLOR_CHAT_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
        )
        text_border.pack(fill="both", expand=True, pady=(0, 14))

        self.text_widget = tk.Text(
            text_border,
            font=FONT_MAIN,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            bd=0,
            highlightthickness=0,
            wrap="word",
            padx=10,
            pady=8,
            cursor="xterm",
            height=8,
            width=46,
        )
        self.text_widget.pack(fill="both", expand=True)

        current_summary = get_summary().strip()
        display_text = current_summary if current_summary else "(No summary yet)"
        self.text_widget.insert("1.0", display_text)

        def block_keys(event):
            if event.state & 4 and event.keysym.lower() in ("c", "a"):
                return None
            if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"):
                return None
            return "break"

        self.text_widget.bind("<KeyPress>", block_keys)
        self.text_widget.bind("<<Paste>>", lambda e: "break")
        self.text_widget.bind("<<Cut>>", lambda e: "break")

        btn_frame = tk.Frame(content_frame, bg=COLOR_BG)
        btn_frame.pack(fill="x")

        self.close_button = tk.Button(
            btn_frame,
            text="Close",
            font=FONT_MAIN,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            activebackground="#e5dfd5",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=4,
            cursor="hand2",
            command=self.destroy,
        )
        self.close_button.pack(side="right")

        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = max(self.winfo_reqwidth(), 400)
        h = max(self.winfo_reqheight(), 240)
        x = px + max((pw - w) // 2, 0)
        y = py + max((ph - h) // 2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(320, 200)

        self.close_button.focus_set()


class EditCharacterDialog(tk.Toplevel):
    """Small window with the current version's text, a Save button and a Cancel button."""

    def __init__(self, parent, version: str, on_save_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.version = version
        self.on_save_callback = on_save_callback
        self.title("Edit character")
        self.configure(bg=COLOR_BG)
        self.resizable(True, True)
        self.transient(parent)

        content_frame = tk.Frame(self, bg=COLOR_BG, padx=20, pady=16)
        content_frame.pack(fill="both", expand=True)

        header_label = tk.Label(
            content_frame,
            text=f"Editing version: {version}",
            font=FONT_BOLD,
            bg=COLOR_BG,
            fg=COLOR_BOT,
        )
        header_label.pack(anchor="w", pady=(0, 8))

        text_border = tk.Frame(
            content_frame,
            bg=COLOR_CHAT_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
        )
        text_border.pack(fill="both", expand=True, pady=(0, 14))

        scrollbar = tk.Scrollbar(text_border)
        scrollbar.pack(side="right", fill="y")

        self.text_widget = tk.Text(
            text_border,
            font=FONT_MAIN,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            bd=0,
            highlightthickness=0,
            wrap="word",
            padx=10,
            pady=8,
            cursor="xterm",
            height=12,
            width=54,
            yscrollcommand=scrollbar.set,
            undo=True,
        )
        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.text_widget.yview)

        current_prompt = load_system_prompt(self.version)
        self.text_widget.insert("1.0", current_prompt)

        btn_frame = tk.Frame(content_frame, bg=COLOR_BG)
        btn_frame.pack(fill="x")

        self.cancel_button = tk.Button(
            btn_frame,
            text="Cancel",
            font=FONT_MAIN,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            activebackground="#e5dfd5",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
            padx=16,
            pady=4,
            cursor="hand2",
            command=self.on_cancel,
        )
        self.cancel_button.pack(side="right", padx=(8, 0))

        self.save_button = tk.Button(
            btn_frame,
            text="Save",
            font=FONT_BOLD,
            bg=COLOR_USER,
            fg="#ffffff",
            activebackground="#452e47",
            activeforeground="#ffffff",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=4,
            cursor="hand2",
            command=self.on_save,
        )
        self.save_button.pack(side="right")

        self.bind("<Escape>", lambda e: self.on_cancel())
        self.bind("<Control-s>", lambda e: self.on_save())

        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = max(self.winfo_reqwidth(), 500)
        h = max(self.winfo_reqheight(), 360)
        x = px + max((pw - w) // 2, 0)
        y = py + max((ph - h) // 2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(360, 240)

        self.text_widget.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.grab_set()

    def on_save(self):
        new_text = self.text_widget.get("1.0", "end-1c").strip()
        save_system_prompt(self.version, new_text)
        if self.on_save_callback:
            self.on_save_callback()
        self.destroy()

    def on_cancel(self):
        self.destroy()


class ShopSheetDialog(tk.Toplevel):
    """Small window showing the current shop sheet text the bot receives."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Shop sheet")
        self.configure(bg=COLOR_BG)
        self.resizable(True, True)
        self.transient(parent)

        content_frame = tk.Frame(self, bg=COLOR_BG, padx=20, pady=16)
        content_frame.pack(fill="both", expand=True)

        header_label = tk.Label(
            content_frame,
            text="Current shop sheet:",
            font=FONT_BOLD,
            bg=COLOR_BG,
            fg=COLOR_BOT,
        )
        header_label.pack(anchor="w", pady=(0, 8))

        text_border = tk.Frame(
            content_frame,
            bg=COLOR_CHAT_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
        )
        text_border.pack(fill="both", expand=True, pady=(0, 14))

        scrollbar = tk.Scrollbar(text_border)
        scrollbar.pack(side="right", fill="y")

        self.text_widget = tk.Text(
            text_border,
            font=FONT_MAIN,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            bd=0,
            highlightthickness=0,
            wrap="word",
            padx=10,
            pady=8,
            cursor="xterm",
            height=14,
            width=56,
            yscrollcommand=scrollbar.set,
        )
        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.text_widget.yview)

        current_sheet = get_current_shop_sheet().strip()
        display_text = current_sheet if current_sheet else "(No shop files found)"
        self.text_widget.insert("1.0", display_text)

        def block_keys(event):
            if event.state & 4 and event.keysym.lower() in ("c", "a"):
                return None
            if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"):
                return None
            return "break"

        self.text_widget.bind("<KeyPress>", block_keys)
        self.text_widget.bind("<<Paste>>", lambda e: "break")
        self.text_widget.bind("<<Cut>>", lambda e: "break")

        def show_popup(event):
            menu = tk.Menu(self.text_widget, tearoff=0)
            try:
                sel = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                sel = display_text

            def copy_text():
                parent.clipboard_clear()
                parent.clipboard_append(sel)

            menu.add_command(label="Copy", command=copy_text)
            menu.tk_popup(event.x_root, event.y_root)

        self.text_widget.bind("<Button-3>", show_popup)

        btn_frame = tk.Frame(content_frame, bg=COLOR_BG)
        btn_frame.pack(fill="x")

        self.close_button = tk.Button(
            btn_frame,
            text="Close",
            font=FONT_MAIN,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            activebackground="#e5dfd5",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=4,
            cursor="hand2",
            command=self.destroy,
        )
        self.close_button.pack(side="right")

        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = max(self.winfo_reqwidth(), 520)
        h = max(self.winfo_reqheight(), 380)
        x = px + max((pw - w) // 2, 0)
        y = py + max((ph - h) // 2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(360, 240)

        self.close_button.focus_set()


class PlaceOrderDialog(tk.Toplevel):
    """Modal confirmation box asking the customer whether to place an order."""

    def __init__(self, parent, order_info: dict):
        super().__init__(parent)
        self.parent = parent
        self.title("Place this order?")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.transient(parent)
        self.result = False

        content_frame = tk.Frame(self, bg=COLOR_BG, padx=24, pady=18)
        content_frame.pack(fill="both", expand=True)

        header_label = tk.Label(
            content_frame,
            text="Place this order?",
            font=FONT_BOLD,
            bg=COLOR_BG,
            fg=COLOR_BOT,
        )
        header_label.pack(anchor="w", pady=(0, 10))

        model = order_info.get("model", "")
        variant = order_info.get("variant", "")
        price = order_info.get("price_rupees", 0)
        delivery_date = order_info.get("delivery_date", "") or "N/A"

        details_text = (
            f"Phone: {model}\n"
            f"Variant: {variant}\n"
            f"Price: ₹{int(price):,}\n"
            f"Delivery date: {delivery_date}"
        )
        details_label = tk.Label(
            content_frame,
            text=details_text,
            font=FONT_MAIN,
            bg=COLOR_BG,
            fg=COLOR_BOT,
            justify="left",
        )
        details_label.pack(anchor="w", pady=(0, 16))

        btn_frame = tk.Frame(content_frame, bg=COLOR_BG)
        btn_frame.pack(fill="x")

        self.no_button = tk.Button(
            btn_frame,
            text="No",
            font=FONT_MAIN,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            activebackground="#e5dfd5",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=4,
            cursor="hand2",
            command=self.on_no,
        )
        self.no_button.pack(side="right", padx=(8, 0))

        self.yes_button = tk.Button(
            btn_frame,
            text="Yes",
            font=FONT_BOLD,
            bg=COLOR_USER,
            fg="#ffffff",
            activebackground="#452e47",
            activeforeground="#ffffff",
            highlightbackground=COLOR_BORDER,
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=4,
            cursor="hand2",
            command=self.on_yes,
        )
        self.yes_button.pack(side="right")

        self.bind("<Escape>", lambda e: self.on_no())

        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = max(self.winfo_reqwidth(), 320)
        h = self.winfo_reqheight()
        x = px + max((pw - w) // 2, 0)
        y = py + max((ph - h) // 2, 0)
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self.on_no)
        self.grab_set()
        self.no_button.focus_set()

    def on_yes(self):
        self.result = True
        self.destroy()

    def on_no(self):
        self.result = False
        self.destroy()


class ChatApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Chatbot")
        self.root.configure(bg=COLOR_BG)

        # Thread-safe event queue
        self.event_queue = queue.Queue()
        self.check_queue()

        # 1. Window opens at half the size of the screen
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        win_w = int(screen_w * 0.5)
        win_h = int(screen_h * 0.5)
        pos_x = (screen_w - win_w) // 2
        pos_y = (screen_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.root.minsize(480, 360)

        self.is_thinking = False
        self.thinking_widget = None

        # Settings state
        self.temperature = DEFAULT_TEMPERATURE
        self.top_p = DEFAULT_TOP_P
        self.max_output_tokens = DEFAULT_MAX_OUTPUT_TOKENS
        self.short_term_memory = DEFAULT_SHORT_TERM_MEMORY
        self.memory_window = DEFAULT_MEMORY_WINDOW
        self.short_term_var = tk.BooleanVar(value=self.short_term_memory)
        self.long_term_memory = DEFAULT_LONG_TERM_MEMORY
        self.long_term_var = tk.BooleanVar(value=self.long_term_memory)
        self.character = DEFAULT_CHARACTER
        self.character_var = tk.BooleanVar(value=self.character)
        self.character_version = DEFAULT_CHARACTER_VERSION
        self.character_version_var = tk.StringVar(value=self.character_version)
        self.today_date = DEFAULT_TODAY_DATE
        self.today_date_var = tk.BooleanVar(value=self.today_date)
        self.shop_files = DEFAULT_SHOP_FILES
        self.shop_files_var = tk.BooleanVar(value=self.shop_files)
        self.structured_answers = DEFAULT_STRUCTURED_ANSWERS
        self.structured_answers_var = tk.BooleanVar(value=self.structured_answers)
        self.phone_lookup = DEFAULT_PHONE_LOOKUP
        self.phone_lookup_var = tk.BooleanVar(value=self.phone_lookup)
        self.step_cap = DEFAULT_STEP_CAP
        self.chat_session_id = 0

        # --- Menu Bar ---
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Settings", menu=self.settings_menu)

        self.settings_menu.add_command(
            label="Temperature...",
            command=self.open_temperature_dialog,
        )
        self.settings_menu.add_command(
            label="Top-P...",
            command=self.open_top_p_dialog,
        )
        self.settings_menu.add_command(
            label="Max tokens...",
            command=self.open_max_tokens_dialog,
        )
        self.settings_menu.add_command(
            label="Top-K: 64 (fixed for this model)",
            state="disabled",
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_checkbutton(
            label="Short-term memory",
            variable=self.short_term_var,
            command=self.on_toggle_short_term,
        )
        self.settings_menu.add_command(
            label="Memory window...",
            command=self.open_memory_window_dialog,
        )
        self.settings_menu.add_checkbutton(
            label="Long-term memory",
            variable=self.long_term_var,
            command=self.on_toggle_long_term,
        )
        self.settings_menu.add_command(
            label="Show memory summary",
            command=self.show_memory_summary,
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_checkbutton(
            label="Character",
            variable=self.character_var,
            command=self.on_toggle_character,
        )
        self.version_menu = tk.Menu(
            self.settings_menu,
            tearoff=0,
            postcommand=self.refresh_version_menu,
        )
        self.settings_menu.add_cascade(
            label="Character version",
            menu=self.version_menu,
        )
        self.settings_menu.add_command(
            label="Edit character...",
            command=self.open_edit_character_dialog,
        )
        self.refresh_version_menu()
        self.settings_menu.add_separator()
        self.settings_menu.add_checkbutton(
            label="Today's date",
            variable=self.today_date_var,
            command=self.on_toggle_today_date,
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_checkbutton(
            label="Shop files",
            variable=self.shop_files_var,
            command=self.on_toggle_shop_files,
        )
        self.settings_menu.add_command(
            label="Show shop sheet",
            command=self.show_shop_sheet,
        )
        self.settings_menu.add_command(
            label="Reload shop files",
            command=self.handle_reload_shop_files,
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_checkbutton(
            label="Phone lookup",
            variable=self.phone_lookup_var,
            command=self.on_toggle_phone_lookup,
        )
        self.settings_menu.add_command(
            label="Step cap...",
            command=self.open_step_cap_dialog,
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_checkbutton(
            label="Structured answers",
            variable=self.structured_answers_var,
            command=self.on_toggle_structured_answers,
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label="New chat",
            command=self.handle_new_chat,
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label="Reset to defaults",
            command=self.reset_to_defaults,
        )

        # --- Top Bar (Token Counter in top right corner & Settings status line) ---
        self.top_bar = tk.Frame(root, height=36, bg=COLOR_BG)
        self.top_bar.pack(side="top", fill="x", padx=18, pady=(8, 2))
        self.top_bar.pack_propagate(False)

        self.settings_label = tk.Label(
            self.top_bar,
            text=self.get_settings_text(),
            font=FONT_SMALL,
            fg=COLOR_TOKEN,
            bg=COLOR_BG,
            anchor="w",
        )
        self.settings_label.pack(side="left")

        self.token_badge = TokenCounterBadge(self.top_bar)
        self.token_badge.pack(side="right")

        # --- Bottom Bar (Typing box & Send button takes 10% of window height) ---
        self.bottom_bar = tk.Frame(root, height=int(win_h * 0.10), bg=COLOR_BG)
        self.bottom_bar.pack(side="bottom", fill="x", padx=18, pady=(4, 12))
        self.bottom_bar.pack_propagate(False)

        self.input_border = tk.Frame(
            self.bottom_bar,
            bg=COLOR_CHAT_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=2,
            bd=0,
        )
        self.input_border.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=4)

        self.entry = tk.Entry(
            self.input_border,
            font=FONT_INPUT,
            bg=COLOR_CHAT_BG,
            fg=COLOR_BOT,
            bd=0,
            highlightthickness=0,
            insertbackground=COLOR_BOT,
        )
        self.entry.pack(fill="both", expand=True, padx=12, pady=6)
        self.entry.bind("<Return>", lambda e: self.send_question())

        self.send_button = tk.Button(
            self.bottom_bar,
            text="Send",
            font=FONT_BOLD,
            bg=COLOR_USER,
            fg="#ffffff",
            activebackground="#452e47",
            activeforeground="#ffffff",
            highlightbackground=COLOR_BORDER,
            highlightthickness=2,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=18,
            command=self.send_question,
        )
        self.send_button.pack(side="right", fill="y", pady=4)

        # --- Chat Area (Takes the rest above typing box) ---
        self.chat_container = tk.Frame(
            root,
            bg=COLOR_CHAT_BG,
            highlightbackground=COLOR_BORDER,
            highlightthickness=2,
            bd=0,
        )
        self.chat_container.pack(side="top", fill="both", expand=True, padx=18, pady=4)

        self.canvas = tk.Canvas(
            self.chat_container,
            bg=COLOR_CHAT_BG,
            highlightthickness=0,
            bd=0,
        )
        self.scrollbar = tk.Scrollbar(
            self.chat_container,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.messages_frame = tk.Frame(self.canvas, bg=COLOR_CHAT_BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.messages_frame,
            anchor="nw",
        )

        # Canvas resizing & scroll configuration
        self.messages_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # Mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        # Responsive 10% bottom bar height
        self.root.bind("<Configure>", self.on_window_resize)

        # Focus entry
        self.entry.focus_set()

    def check_queue(self):
        while not self.event_queue.empty():
            try:
                fn, args = self.event_queue.get_nowait()
                fn(*args)
            except queue.Empty:
                break
        self.root.after(40, self.check_queue)

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_window_resize(self, event):
        if event.widget == self.root:
            new_h = max(int(event.height * 0.10), 46)
            if self.bottom_bar.cget("height") != new_h:
                self.bottom_bar.configure(height=new_h)

    def get_settings_text(self) -> str:
        short_term_state = "Short-term on" if self.short_term_memory else "Short-term off"
        in_window = min(len(history), self.memory_window)
        short_term_str = f"{short_term_state}, {self.memory_window} exchanges, {in_window} in the window"

        long_term_state = "Long-term on" if self.long_term_memory else "Long-term off"
        summarized_count = get_summarized_count()
        long_term_str = f"{long_term_state}, {summarized_count} summarised"

        character_str = get_character_status(self.character, self.character_version)
        date_str = get_date_status(self.today_date)
        shop_str = get_shop_status(self.shop_files)
        phone_str = get_phone_lookup_status(self.phone_lookup)
        step_cap_str = get_step_cap_status(self.step_cap)

        return (
            f"Temperature {self.temperature:.1f} · "
            f"Top-P {round(self.top_p, 2)} · "
            f"Max tokens {int(self.max_output_tokens)} · "
            f"{short_term_str}. {long_term_str} · "
            f"{character_str} · "
            f"{date_str} · "
            f"{shop_str} · "
            f"{phone_str} · "
            f"{step_cap_str}"
        )

    def update_settings_display(self):
        self.settings_label.config(text=self.get_settings_text())

    def on_toggle_character(self):
        self.character = self.character_var.get()
        self.update_settings_display()

    def on_toggle_today_date(self):
        self.today_date = self.today_date_var.get()
        self.update_settings_display()

    def on_toggle_shop_files(self):
        self.shop_files = self.shop_files_var.get()
        self.update_settings_display()

    def on_toggle_structured_answers(self):
        self.structured_answers = self.structured_answers_var.get()

    def on_toggle_phone_lookup(self):
        self.phone_lookup = self.phone_lookup_var.get()
        self.update_settings_display()

    def open_step_cap_dialog(self):
        dlg = SliderDialog(
            self.root,
            title="Step cap",
            current_val=self.step_cap,
            from_=1,
            to=10,
            resolution=1,
            is_int=True,
        )
        if dlg.winfo_exists():
            self.root.wait_window(dlg)
        if dlg.result is not None:
            self.step_cap = dlg.result
            self.update_settings_display()

    def show_shop_sheet(self):
        ShopSheetDialog(self.root)

    def handle_reload_shop_files(self):
        def worker():
            reload_shop_files()
            self.event_queue.put((self.update_settings_display, ()))
        threading.Thread(target=worker, daemon=True).start()

    def refresh_version_menu(self):
        self.version_menu.delete(0, "end")
        versions = get_character_versions()
        if self.character_version not in versions and versions:
            self.character_version = versions[0]
            self.character_version_var.set(self.character_version)
        for v in versions:
            self.version_menu.add_radiobutton(
                label=v,
                variable=self.character_version_var,
                value=v,
                command=self.on_select_version,
            )

    def on_select_version(self):
        self.character_version = self.character_version_var.get()
        self.update_settings_display()

    def open_edit_character_dialog(self):
        EditCharacterDialog(
            self.root,
            version=self.character_version,
            on_save_callback=self.update_settings_display,
        )

    def on_toggle_short_term(self):
        self.short_term_memory = self.short_term_var.get()
        self.update_settings_display()

    def on_toggle_long_term(self):
        self.long_term_memory = self.long_term_var.get()
        if self.long_term_memory:
            def catch_up_worker():
                catch_up_summary(
                    short_term_memory=self.short_term_memory,
                    memory_window=self.memory_window,
                    long_term_memory=self.long_term_memory,
                )
                self.event_queue.put((self.update_settings_display, ()))
                self.event_queue.put((self.token_badge.refresh, ()))
            threading.Thread(target=catch_up_worker, daemon=True).start()
        self.update_settings_display()

    def show_memory_summary(self):
        MemorySummaryDialog(self.root)

    def open_temperature_dialog(self):
        dlg = SliderDialog(
            self.root,
            title="Temperature",
            current_val=self.temperature,
            from_=0.0,
            to=2.0,
            resolution=0.1,
            is_int=False,
        )
        if dlg.winfo_exists():
            self.root.wait_window(dlg)
        if dlg.result is not None:
            self.temperature = dlg.result
            self.update_settings_display()

    def open_top_p_dialog(self):
        dlg = SliderDialog(
            self.root,
            title="Top-P",
            current_val=self.top_p,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            is_int=False,
        )
        if dlg.winfo_exists():
            self.root.wait_window(dlg)
        if dlg.result is not None:
            self.top_p = dlg.result
            self.update_settings_display()

    def open_max_tokens_dialog(self):
        dlg = SliderDialog(
            self.root,
            title="Max tokens",
            current_val=self.max_output_tokens,
            from_=10,
            to=2000,
            resolution=10,
            is_int=True,
        )
        if dlg.winfo_exists():
            self.root.wait_window(dlg)
        if dlg.result is not None:
            self.max_output_tokens = dlg.result
            self.update_settings_display()

    def open_memory_window_dialog(self):
        dlg = MemoryWindowDialog(
            self.root,
            current_val=self.memory_window,
        )
        if dlg.winfo_exists():
            self.root.wait_window(dlg)
        if dlg.result is not None:
            self.memory_window = dlg.result
            if self.long_term_memory:
                def catch_up_worker():
                    catch_up_summary(
                        short_term_memory=self.short_term_memory,
                        memory_window=self.memory_window,
                        long_term_memory=self.long_term_memory,
                    )
                    self.event_queue.put((self.update_settings_display, ()))
                    self.event_queue.put((self.token_badge.refresh, ()))
                threading.Thread(target=catch_up_worker, daemon=True).start()
            self.update_settings_display()

    def handle_new_chat(self):
        self.chat_session_id += 1
        new_chat()
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        self.thinking_widget = None
        self.is_thinking = False
        self.send_button.config(state="normal")
        self.canvas.configure(scrollregion=(0, 0, 0, 0))
        self.canvas.yview_moveto(0.0)
        self.update_settings_display()
        self.entry.focus_set()

    def reset_to_defaults(self):
        self.temperature = DEFAULT_TEMPERATURE
        self.top_p = DEFAULT_TOP_P
        self.max_output_tokens = DEFAULT_MAX_OUTPUT_TOKENS
        self.short_term_memory = DEFAULT_SHORT_TERM_MEMORY
        self.short_term_var.set(DEFAULT_SHORT_TERM_MEMORY)
        self.memory_window = DEFAULT_MEMORY_WINDOW
        self.long_term_memory = DEFAULT_LONG_TERM_MEMORY
        self.long_term_var.set(DEFAULT_LONG_TERM_MEMORY)
        self.character = DEFAULT_CHARACTER
        self.character_var.set(DEFAULT_CHARACTER)
        self.character_version = DEFAULT_CHARACTER_VERSION
        self.character_version_var.set(DEFAULT_CHARACTER_VERSION)
        self.today_date = DEFAULT_TODAY_DATE
        self.today_date_var.set(DEFAULT_TODAY_DATE)
        self.shop_files = DEFAULT_SHOP_FILES
        self.shop_files_var.set(DEFAULT_SHOP_FILES)
        self.structured_answers = DEFAULT_STRUCTURED_ANSWERS
        self.structured_answers_var.set(DEFAULT_STRUCTURED_ANSWERS)
        self.phone_lookup = DEFAULT_PHONE_LOOKUP
        self.phone_lookup_var.set(DEFAULT_PHONE_LOOKUP)
        self.step_cap = DEFAULT_STEP_CAP
        self.refresh_version_menu()
        self.update_settings_display()

    def scroll_to_bottom(self):
        self.root.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def send_question(self):
        if self.is_thinking:
            return
        question = self.entry.get().strip()
        if not question:
            return

        self.entry.delete(0, "end")
        self.is_thinking = True
        self.send_button.config(state="disabled")

        # Snapshot current settings and session for this request
        temp = self.temperature
        top_p = self.top_p
        max_tokens = self.max_output_tokens
        mem_on = self.short_term_memory
        mem_win = self.memory_window
        long_mem_on = self.long_term_memory
        char_on = self.character
        char_ver = self.character_version
        today_date_on = self.today_date
        shop_on = self.shop_files
        structured_on = self.structured_answers
        phone_lookup_on = self.phone_lookup
        step_cap_val = self.step_cap
        session_id = self.chat_session_id

        # 1. Add user bubble to chat (left side)
        self.add_user_bubble(question)

        # 2. Show "Thinking..." in the chat
        self.show_thinking()

        # 3. Call ask() in background thread to keep UI responsive
        def confirm_order_from_ui(order_info: dict) -> bool:
            if session_id != self.chat_session_id:
                return False
            done = threading.Event()
            answer = [False]

            def show_dialog():
                if session_id != self.chat_session_id:
                    done.set()
                    return
                dlg = PlaceOrderDialog(self.root, order_info)
                self.root.wait_window(dlg)
                answer[0] = bool(dlg.result)
                done.set()

            self.event_queue.put((show_dialog, ()))
            done.wait()
            return answer[0]

        def worker():
            try:
                res = ask(
                    question,
                    temperature=temp,
                    top_p=top_p,
                    max_output_tokens=max_tokens,
                    short_term_memory=mem_on,
                    memory_window=mem_win,
                    long_term_memory=long_mem_on,
                    character=char_on,
                    character_version=char_ver,
                    today_date=today_date_on,
                    shop_files=shop_on,
                    structured_answers=structured_on,
                    phone_lookup=phone_lookup_on,
                    step_cap=step_cap_val,
                    confirm_order=confirm_order_from_ui,
                )
                reply = res.reply if hasattr(res, "reply") else res[0]
                tokens = res.token_usage if hasattr(res, "token_usage") else res[1]
                tin, tout = tokens
                items = res.items if hasattr(res, "items") else []
                tool_calls = res.tool_calls if hasattr(res, "tool_calls") else []
                steps_used = res.steps_used if hasattr(res, "steps_used") else 0
                hit_step_cap = res.hit_step_cap if hasattr(res, "hit_step_cap") else False
                is_stopped = False
                if hasattr(res, "stopped_max_tokens"):
                    is_stopped = bool(res.stopped_max_tokens)
                elif hasattr(res, "finish_reason"):
                    is_stopped = "MAX_TOKENS" in str(res.finish_reason).upper()
                self.event_queue.put(
                    (
                        self.handle_reply,
                        (
                            reply,
                            items,
                            tool_calls,
                            steps_used,
                            step_cap_val,
                            hit_step_cap,
                            tin,
                            tout,
                            is_stopped,
                            temp,
                            top_p,
                            max_tokens,
                            session_id,
                        ),
                    )
                )
            except Exception as e:
                self.event_queue.put((self.handle_error, (e, session_id)))

        threading.Thread(target=worker, daemon=True).start()

    def add_user_bubble(self, question: str):
        row = tk.Frame(self.messages_frame, bg=COLOR_CHAT_BG)
        row.pack(fill="x", padx=16, pady=6)

        bubble_text = f"User : {question}"
        max_w = max(int(self.canvas.winfo_width() * 0.65), 260)
        bubble = create_bubble_canvas(row, bubble_text, is_user=True, max_width=max_w)
        bubble.pack(side="left")
        self.scroll_to_bottom()

    def show_thinking(self):
        row = tk.Frame(self.messages_frame, bg=COLOR_CHAT_BG)
        row.pack(fill="x", padx=16, pady=4)
        lbl = tk.Label(
            row,
            text="Thinking...",
            font=FONT_MAIN,
            fg=COLOR_TOKEN,
            bg=COLOR_CHAT_BG,
        )
        lbl.pack(side="right")
        self.thinking_widget = row
        self.scroll_to_bottom()

    def hide_thinking(self):
        if self.thinking_widget:
            self.thinking_widget.destroy()
            self.thinking_widget = None

    @staticmethod
    def format_tool_call_line(tc: dict, index: int) -> str:
        step = tc.get("step", index)
        name = tc.get("name", "")
        args = tc.get("args", {}) or {}
        if "error" in tc:
            err = str(tc["error"]).strip()
            if name == "find_phone":
                arg_str = f'"{args.get("model", "")}"'
            elif name == "list_phones":
                brand = args.get("brand", "")
                in_stock = bool(args.get("in_stock_only", False))
                arg_str = f'"{brand}", in stock' if in_stock else f'"{brand}"'
            elif name == "check_delivery":
                arg_str = f'"{args.get("product_id", "")}"'
            elif name == "place_order":
                arg_str = f'"{args.get("product_id", "")}"'
            else:
                arg_str = str(args)
            return f"Step {step}: {name}({arg_str}) -> error: {err}"
        if name == "place_order":
            pid = args.get("product_id", "")
            if tc.get("confirmed") is False:
                return f'Step {step}: place_order("{pid}") -> customer said no'
            result = tc.get("result", {}) or {}
            order_num = result.get("order_number", "")
            return f'Step {step}: place_order("{pid}") -> customer said yes -> {order_num}'
        if name == "find_phone":
            model = args.get("model", "")
            row_count = tc.get("row_count", 0)
            row_label = "row" if row_count == 1 else "rows"
            return f'Step {step}: find_phone("{model}") -> {row_count} {row_label}'
        if name == "list_phones":
            brand = args.get("brand", "")
            in_stock = bool(args.get("in_stock_only", False))
            row_count = tc.get("row_count", 0)
            row_label = "row" if row_count == 1 else "rows"
            arg_str = f'"{brand}", in stock' if in_stock else f'"{brand}"'
            return f"Step {step}: list_phones({arg_str}) -> {row_count} {row_label}"
        if name == "check_delivery":
            pid = args.get("product_id", "")
            result = tc.get("result", {}) or {}
            if "error" in result:
                summary = "not found"
            elif str(result.get("status", "")).lower() == "out of stock":
                restock = result.get("restock_date", "")
                summary = f"Out of stock, restock {restock}".strip()
            else:
                status = result.get("status", "")
                days = result.get("delivery_days", "")
                summary = f"{status}, {days} days" if days != "" else status
            return f'Step {step}: check_delivery("{pid}") -> {summary}'
        return f"Step {step}: {name}({args})"

    def handle_reply(
        self,
        reply: str,
        items: list = None,
        tool_calls: list = None,
        steps_used: int = 0,
        step_cap: int = DEFAULT_STEP_CAP,
        hit_step_cap: bool = False,
        tokens_in: int = 0,
        tokens_out: int = 0,
        stopped_max_tokens: bool = False,
        temp: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        max_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        session_id: int = 0,
    ):
        if session_id != self.chat_session_id:
            return
        self.hide_thinking()
        self.is_thinking = False
        self.send_button.config(state="normal")
        self.entry.focus_set()

        # 1. Add bot bubble (right side)
        row = tk.Frame(self.messages_frame, bg=COLOR_CHAT_BG)
        row.pack(fill="x", padx=16, pady=(6, 2))

        bubble_text = f"Bot : {reply}"
        max_w = max(int(self.canvas.winfo_width() * 0.65), 260)
        bubble = create_bubble_canvas(row, bubble_text, is_user=False, max_width=max_w)
        bubble.pack(side="right")

        # 2. Under it, when items is not empty, one line our code works out itself:
        # Total (our code): 1,298 rupees (price times quantity, added up).
        if items:
            total = sum(
                (item.price_rupees if hasattr(item, "price_rupees") else item["price_rupees"])
                * (item.quantity if hasattr(item, "quantity") else item["quantity"])
                for item in items
            )
            total_row = tk.Frame(self.messages_frame, bg=COLOR_CHAT_BG)
            total_row.pack(fill="x", padx=16, pady=(0, 2))

            total_lbl = tk.Label(
                total_row,
                text=f"Total (our code): {total:,} rupees",
                font=FONT_MAIN,
                fg=COLOR_BOT,
                bg=COLOR_CHAT_BG,
            )
            total_lbl.pack(side="right", padx=10)

        # 3. One numbered grey line per tool call under the reply, plus Steps: X of Y
        if tool_calls:
            for idx, tc in enumerate(tool_calls, start=1):
                tool_row = tk.Frame(self.messages_frame, bg=COLOR_CHAT_BG)
                tool_row.pack(fill="x", padx=16, pady=(0, 2))
                tool_lbl = tk.Label(
                    tool_row,
                    text=self.format_tool_call_line(tc, idx),
                    font=FONT_SMALL,
                    fg=COLOR_TOKEN,
                    bg=COLOR_CHAT_BG,
                )
                tool_lbl.pack(side="right", padx=10)

        if tool_calls or hit_step_cap or steps_used > 1:
            steps_row = tk.Frame(self.messages_frame, bg=COLOR_CHAT_BG)
            steps_row.pack(fill="x", padx=16, pady=(0, 2))
            steps_lbl = tk.Label(
                steps_row,
                text=f"Steps: {steps_used} of {step_cap}",
                font=FONT_SMALL,
                fg=COLOR_TOKEN,
                bg=COLOR_CHAT_BG,
            )
            steps_lbl.pack(side="right", padx=10)

        # 4. One small grey line under reply: tokens in and tokens out, settings used, and stopped: max tokens
        token_row = tk.Frame(self.messages_frame, bg=COLOR_CHAT_BG)
        token_row.pack(fill="x", padx=16, pady=(0, 6))

        settings_str = (
            f"Temperature {temp:.1f} · "
            f"Top-P {round(top_p, 2)} · "
            f"Max tokens {int(max_tokens)}"
        )
        parts = [f"{tokens_in} in, {tokens_out} out", settings_str]
        if stopped_max_tokens:
            parts.append("stopped: max tokens")
        lbl_text = " · ".join(parts)

        token_lbl = tk.Label(
            token_row,
            text=lbl_text,
            font=FONT_SMALL,
            fg=COLOR_TOKEN,
            bg=COLOR_CHAT_BG,
        )
        token_lbl.pack(side="right", padx=10)

        # 3. Update token counter badge in top right corner & status line
        self.token_badge.refresh()
        self.update_settings_display()
        self.scroll_to_bottom()

    def handle_error(self, err: Exception, session_id: int = 0):
        if session_id != self.chat_session_id:
            return
        self.hide_thinking()
        self.is_thinking = False
        self.send_button.config(state="normal")
        self.entry.focus_set()

        # Show short plain message in chat in error colour clay #a8441f
        error_msg = format_error_message(err)
        row = tk.Frame(self.messages_frame, bg=COLOR_CHAT_BG)
        row.pack(fill="x", padx=16, pady=6)

        err_label = tk.Label(
            row,
            text=error_msg,
            font=FONT_MAIN,
            fg=COLOR_ERROR,
            bg=COLOR_CHAT_BG,
            wraplength=max(int(self.canvas.winfo_width() * 0.8), 300),
            justify="center",
        )
        err_label.pack(side="top", pady=4)
        self.scroll_to_bottom()


def main():
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
