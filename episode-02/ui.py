import queue
import threading
import tkinter as tk
from bot import ask, usage

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

        # --- Top Bar (Token Counter in top right corner) ---
        self.top_bar = tk.Frame(root, height=36, bg=COLOR_BG)
        self.top_bar.pack(side="top", fill="x", padx=18, pady=(8, 2))
        self.top_bar.pack_propagate(False)

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

        # 1. Add user bubble to chat (left side)
        self.add_user_bubble(question)

        # 2. Show "Thinking..." in the chat
        self.show_thinking()

        # 3. Call ask() in background thread to keep UI responsive
        def worker():
            try:
                reply, tokens = ask(question)
                tin, tout = tokens
                self.event_queue.put((self.handle_reply, (reply, tin, tout)))
            except Exception as e:
                self.event_queue.put((self.handle_error, (e,)))

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

    def handle_reply(self, reply: str, tokens_in: int, tokens_out: int):
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

        # 2. One small grey line under reply: tokens in and tokens out
        token_row = tk.Frame(self.messages_frame, bg=COLOR_CHAT_BG)
        token_row.pack(fill="x", padx=16, pady=(0, 6))

        token_lbl = tk.Label(
            token_row,
            text=f"{tokens_in} in, {tokens_out} out",
            font=FONT_SMALL,
            fg=COLOR_TOKEN,
            bg=COLOR_CHAT_BG,
        )
        token_lbl.pack(side="right", padx=10)

        # 3. Update token counter badge in top right corner
        self.token_badge.refresh()
        self.scroll_to_bottom()

    def handle_error(self, err: Exception):
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
