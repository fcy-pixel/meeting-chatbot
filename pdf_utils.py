import os
import base64
import fitz  # PyMuPDF
import requests

# PDF 儲存資料夾
PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)


def _github_headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def _github_upload(token: str, repo: str, filename: str, pdf_bytes: bytes):
    """上傳檔案到 GitHub repo 的 pdfs/ 資料夾。"""
    url = f"https://api.github.com/repos/{repo}/contents/pdfs/{filename}"
    headers = _github_headers(token)

    # 檢查檔案是否已存在（需要 sha 來更新）
    resp = requests.get(url, headers=headers, timeout=15)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    payload = {
        "message": f"上傳會議紀錄: {filename}",
        "content": base64.b64encode(pdf_bytes).decode("utf-8"),
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()


def _github_delete(token: str, repo: str, filename: str):
    """從 GitHub repo 刪除檔案。"""
    url = f"https://api.github.com/repos/{repo}/contents/pdfs/{filename}"
    headers = _github_headers(token)

    # 需要 sha 才能刪除
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return  # 檔案不存在，跳過
    sha = resp.json()["sha"]

    payload = {
        "message": f"刪除會議紀錄: {filename}",
        "sha": sha,
        "branch": "main",
    }
    resp = requests.delete(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()


def upload_pdf(pdf_bytes: bytes, filename: str, github_token: str = "", github_repo: str = ""):
    """儲存 PDF 到本機，並同步到 GitHub。"""
    filepath = os.path.join(PDF_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)

    if github_token and github_repo:
        _github_upload(github_token, github_repo, filename, pdf_bytes)


def delete_pdf(filename: str, github_token: str = "", github_repo: str = ""):
    """刪除 PDF，並從 GitHub 同步刪除。"""
    filepath = os.path.join(PDF_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    if github_token and github_repo:
        _github_delete(github_token, github_repo, filename)


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
