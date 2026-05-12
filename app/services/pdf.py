import fitz
import os

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_pdf(file_bytes: bytes, filename: str) -> str:
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return file_path

def extract_text(file_path: str) -> tuple[str, int]:
    doc = fitz.open(file_path)
    total_pages = len(doc)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text, total_pages