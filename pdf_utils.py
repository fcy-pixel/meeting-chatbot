import os
import fitz  # PyMuPDF

# PDF 儲存資料夾
PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)


def upload_pdf(pdf_bytes: bytes, filename: str):
    """儲存 PDF 到本機 pdfs/ 資料夾。"""
    filepath = os.path.join(PDF_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)


def delete_pdf(filename: str):
    """從 pdfs/ 資料夾刪除 PDF。"""
    filepath = os.path.join(PDF_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)


def list_pdfs() -> list[dict]:
    """列出 pdfs/ 資料夾中的所有 PDF。"""
    files = []
    for name in sorted(os.listdir(PDF_DIR)):
        if name.lower().endswith(".pdf"):
            filepath = os.path.join(PDF_DIR, name)
            modified = os.path.getmtime(filepath)
            files.append({
                "name": name,
                "path": filepath,
                "modified": str(modified),
            })
    return files


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """從 PDF 位元組中提取文字。"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def load_all_meeting_docs() -> list[dict]:
    """載入 pdfs/ 資料夾中所有 PDF 的文字內容。"""
    pdf_files = list_pdfs()
    docs = []
    for f in pdf_files:
        try:
            with open(f["path"], "rb") as fh:
                pdf_bytes = fh.read()
            text = extract_text_from_pdf(pdf_bytes)
            if text.strip():
                docs.append({
                    "name": f["name"],
                    "modified": f["modified"],
                    "text": text,
                })
        except Exception as e:
            docs.append({
                "name": f["name"],
                "modified": f["modified"],
                "text": f"[無法讀取此檔案: {e}]",
            })
    return docs
