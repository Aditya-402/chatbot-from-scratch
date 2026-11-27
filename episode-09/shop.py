import os
from pypdf import PdfReader
from bs4 import BeautifulSoup

SHOP_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "prompts", "shop"
)


def read_pdf(file_path: str) -> str:
    """Extracts text of every page from a PDF file using pypdf."""
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            pages.append(txt)
    return "\n".join(pages).strip()


def read_html(file_path: str) -> str:
    """Extracts visible text without tags from an HTML file using BeautifulSoup."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    soup = BeautifulSoup(content, "html.parser")
    for elem in soup(["script", "style"]):
        elem.decompose()
    return soup.get_text(separator="\n", strip=True)


def read_text_file(file_path: str) -> str:
    """Reads a text or markdown file as it is."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().strip()


def read_shop_file(file_path: str) -> str:
    """Reads a shop file and converts it to plain text based on its extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return read_pdf(file_path)
    elif ext in (".html", ".htm"):
        return read_html(file_path)
    else:
        return read_text_file(file_path)


def load_shop_files(shop_dir: str = SHOP_DIR) -> dict[str, str]:
    """Reads every file in prompts/shop/ and returns a dict mapping file name to plain text."""
    if not os.path.isdir(shop_dir):
        return {}
    files_data = {}
    for fname in sorted(os.listdir(shop_dir)):
        fpath = os.path.join(shop_dir, fname)
        if os.path.isfile(fpath):
            try:
                files_data[fname] = read_shop_file(fpath)
            except Exception as e:
                files_data[fname] = f"(Error reading {fname}: {e})"
    return files_data


def build_shop_sheet(files_data: dict[str, str]) -> str:
    """Puts the texts together into one shop sheet, each part starting with its file name."""
    parts = []
    for fname, text in files_data.items():
        parts.append(f"{fname}:\n{text}")
    return "\n\n".join(parts)


def get_shop_sheet(shop_dir: str = SHOP_DIR) -> str:
    """Reads all files in shop_dir and returns the combined shop sheet."""
    files_data = load_shop_files(shop_dir)
    return build_shop_sheet(files_data)


def count_shop_files(shop_dir: str = SHOP_DIR) -> int:
    """Returns the count of shop files found in shop_dir."""
    if not os.path.isdir(shop_dir):
        return 0
    return sum(
        1 for f in os.listdir(shop_dir) if os.path.isfile(os.path.join(shop_dir, f))
    )

