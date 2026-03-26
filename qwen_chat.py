from openai import OpenAI

# Qwen International API (DashScope compatible endpoint)
QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen-plus"


def get_qwen_client(api_key: str) -> OpenAI:
    """建立 Qwen API 客戶端（使用 OpenAI 相容介面）。"""
    return OpenAI(api_key=api_key, base_url=QWEN_BASE_URL)


def build_context(docs: list[dict], max_chars: int = 60000) -> str:
    """將會議紀錄合併成上下文文字，控制在 token 限制內。"""
    parts = []
    total = 0
    for doc in docs:
        header = f"===== 檔案：{doc['name']}（修改時間：{doc['modified']}）=====\n"
        content = doc["text"]
        if total + len(header) + len(content) > max_chars:
            remaining = max_chars - total - len(header)
            if remaining > 200:
                parts.append(header + content[:remaining] + "\n...(截斷)")
            break
        parts.append(header + content)
        total += len(header) + len(content)
    return "\n\n".join(parts)


SYSTEM_PROMPT = """你是一個專業的學校會議紀錄助手。你的任務是根據提供的會議紀錄 PDF 內容，準確回答老師的問題。

規則：
1. 只根據提供的會議紀錄內容回答，不要編造資訊
2. 如果會議紀錄中沒有相關資訊，請明確告知
3. 回答時引用具體的會議名稱和日期
4. 使用繁體中文回答
5. 回答要清晰、有條理"""


def chat_with_docs(client: OpenAI, docs: list[dict], messages: list[dict]) -> str:
    """根據會議紀錄和對話歷史回答問題。"""
    context = build_context(docs)

    system_msg = SYSTEM_PROMPT + f"\n\n以下是會議紀錄內容：\n\n{context}"

    api_messages = [{"role": "system", "content": system_msg}]
    api_messages.extend(messages)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=api_messages,
        temperature=0.3,
        max_tokens=2000,
    )
    return response.choices[0].message.content
