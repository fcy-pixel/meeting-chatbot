import fitz  # PyMuPDF
import firebase_admin
from firebase_admin import credentials, storage


def init_firebase(firebase_config: dict, bucket_name: str):
    """初始化 Firebase（只初始化一次）。"""
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})


def upload_pdf(pdf_bytes: bytes, filename: str):
    """上傳 PDF 到 Firebase Storage。"""
    bucket = storage.bucket()
    blob = bucket.blob(f"meeting_pdfs/{filename}")
    blob.upload_from_string(pdf_bytes, content_type="application/pdf")


def delete_pdf(filename: str):
    """從 Firebase Storage 刪除 PDF。"""
    bucket = storage.bucket()
    blob = bucket.blob(f"meeting_pdfs/{filename}")
    blob.delete()


def list_pdfs() -> list[dict]:
    """列出 Firebase Storage 中所有 PDF。"""
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix="meeting_pdfs/")
    files = []
    for blob in blobs:
        if blob.name.endswith(".pdf"):
            files.append({
                "name": blob.name.replace("meeting_pdfs/", ""),
                "full_path": blob.name,
                "modified": str(blob.updated) if blob.updated else "",
            })
    return files


def download_pdf(full_path: str) -> bytes:
    """從 Firebase Storage 下載 PDF。"""
    bucket = storage.bucket()
    blob = bucket.blob(full_path)
    return blob.download_as_bytes()


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """從 PDF 位元組中提取文字。"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def load_all_meeting_docs() -> list[dict]:
    """從 Firebase 載入所有 PDF 並提取文字。"""
    pdf_files = list_pdfs()
    docs = []
    for f in pdf_files:
        try:
            pdf_bytes = download_pdf(f["full_path"])
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
