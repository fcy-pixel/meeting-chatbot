import streamlit as st
from pdf_utils import upload_pdf, delete_pdf, list_pdfs, load_all_meeting_docs
from qwen_chat import get_qwen_client, chat_with_docs

# ---------- 頁面設定 ----------
st.set_page_config(page_title="中華基督教會基慈小學 — 校務會議紀錄查詢 Empowerd by Qwen AI", page_icon="📋", layout="wide")

# ---------- 讀取設定 ----------
QWEN_API_KEY = st.secrets.get("QWEN_API_KEY", "") or ""
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "") or ""
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "") or ""
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "") or ""

# ---------- 側邊欄 ----------
with st.sidebar:
    st.header("📋 中華基督教會基慈小學")
    st.caption("校務會議紀錄查詢 Empowerd by Qwen AI")

    if not QWEN_API_KEY:
        QWEN_API_KEY = st.text_input("Qwen API Key", type="password")
    if QWEN_API_KEY:
        st.success("✅ Qwen API Key 已設定")

    st.divider()
    mode = st.radio("模式", ["💬 聊天", "🔧 管理員"], horizontal=True)

    if mode == "🔧 管理員":
        pwd = st.text_input("管理員密碼", type="password")
        if pwd and pwd != ADMIN_PASSWORD:
            st.error("密碼錯誤")
            mode = "💬 聊天"
        elif not pwd:
            mode = "💬 聊天"

    st.divider()
    if st.button("🔄 重新載入文件", use_container_width=True):
        st.session_state.pop("docs", None)
        st.rerun()

# ==========================================
# 管理員模式：上傳 / 刪除 PDF
# ==========================================
if mode == "🔧 管理員":
    st.title("🔧 管理員 — 管理會議紀錄")

    st.subheader("📤 上傳 PDF")
    uploaded_files = st.file_uploader(
        "選擇 PDF 檔案", type="pdf", accept_multiple_files=True
    )
    if uploaded_files and st.button("確認上傳", type="primary"):
        for uf in uploaded_files:
            with st.spinner(f"上傳 {uf.name}（同步到 GitHub）..."):
                upload_pdf(uf.getvalue(), uf.name, GITHUB_TOKEN, GITHUB_REPO)
            st.success(f"✅ 已上傳：{uf.name}")
        st.session_state.pop("docs", None)
        st.rerun()

    st.divider()
    st.subheader("📄 已儲存的檔案")
    existing_files = list_pdfs()
    if not existing_files:
        st.info("目前沒有任何 PDF 檔案")
    else:
        for f in existing_files:
            col1, col2 = st.columns([4, 1])
            col1.write(f"📎 {f['name']}")
            if col2.button("🗑️", key=f"del_{f['name']}", help=f"刪除 {f['name']}"):
                delete_pdf(f["name"], GITHUB_TOKEN, GITHUB_REPO)
                st.success(f"已刪除：{f['name']}")
                st.session_state.pop("docs", None)
                st.rerun()
    st.stop()

# ==========================================
# 聊天模式
# ==========================================
st.title("📋 中華基督教會基慈小學")
st.subheader("校務會議紀錄查詢 Empowerd by Qwen AI")
st.caption("根據已上傳的會議紀錄 PDF，使用 AI 回答老師問題")

if not QWEN_API_KEY:
    st.info("👈 請在側邊欄輸入 Qwen API Key")
    st.stop()

# ---------- 載入會議紀錄 ----------
if "docs" not in st.session_state:
    with st.spinner("正在載入會議紀錄..."):
        try:
            docs = load_all_meeting_docs()
            st.session_state["docs"] = docs
        except Exception as e:
            st.error(f"載入失敗：{e}")
            st.stop()

docs = st.session_state["docs"]

with st.sidebar:
    st.divider()
    st.subheader(f"📄 已載入 {len(docs)} 份文件")
    for d in docs:
        st.text(f"• {d['name']}")

if not docs:
    st.warning("目前沒有會議紀錄，請管理員上傳 PDF。")
    st.stop()

# ---------- 對話介面 ----------
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("請輸入您的問題（例如：上次會議決定了什麼？）"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                client = get_qwen_client(QWEN_API_KEY)
                answer = chat_with_docs(client, docs, st.session_state["messages"])
                st.markdown(answer)
                st.session_state["messages"].append({"role": "assistant", "content": answer})
            except Exception as e:
                error_msg = f"回覆失敗：{e}"
                st.error(error_msg)
                st.session_state["messages"].append({"role": "assistant", "content": error_msg})
