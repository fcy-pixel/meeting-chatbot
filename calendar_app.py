import streamlit as st
import json
import os
import re
from datetime import datetime, timedelta, date
from collections import defaultdict

try:
    from streamlit_calendar import calendar as st_calendar
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# ---------- 常數 ----------
EVENTS_FILE = os.path.join(os.path.dirname(__file__), "calendar_events.json")

CATEGORY_COLORS = {
    "假期":    "#e74c3c",
    "評估":    "#e67e22",
    "校外活動": "#3498db",
    "活動":    "#2ecc71",
    "交流":    "#9b59b6",
    "會議":    "#1abc9c",
    "校務":    "#7f8c8d",
    "課外活動": "#f39c12",
    "AI新增":  "#8e44ad",
}

PRELOADED_EVENTS = [
    {"id": "p01", "title": "元宵節",                           "start": "2026-03-03",                  "color": "#e74c3c",  "category": "假期"},
    {"id": "p02", "title": "3-6年級填寫KPM持份者學生問卷",         "start": "2026-03-04", "end": "2026-03-06", "color": "#e67e22",  "category": "校務"},
    {"id": "p03", "title": "派發温習材料",                       "start": "2026-03-06",                  "color": "#7f8c8d",  "category": "校務"},
    {"id": "p04", "title": "星期六課外活動開始",                   "start": "2026-03-07",                  "color": "#f39c12",  "category": "課外活動"},
    {"id": "p05", "title": "區本活動開始",                       "start": "2026-03-07",                  "color": "#2ecc71",  "category": "活動"},
    {"id": "p06", "title": "法團校董會會議 (6:30pm)",             "start": "2026-03-14",                  "color": "#1abc9c",  "category": "會議"},
    {"id": "p07", "title": "二至六年級評估二 / 一年級主題式學習",     "start": "2026-03-16", "end": "2026-03-21", "color": "#e67e22",  "category": "評估"},
    {"id": "p08", "title": "「新時代築夢計劃（人工智能）」校內問卷評估（前測）", "start": "2026-03-18T12:00:00", "color": "#9b59b6", "category": "活動"},
    {"id": "p09", "title": "一、四年級校外科學探索活動 / 賽馬會大熊貓之旅", "start": "2026-03-18", "color": "#3498db", "category": "校外活動"},
    {"id": "p10", "title": "Tales of Character: 一、二年級英文語常會活動", "start": "2026-03-25", "color": "#2ecc71", "category": "活動", "description": "1:25-2:55 p.m."},
    {"id": "p11", "title": "境外交流（冲繩）四天",                 "start": "2026-03-26", "end": "2026-03-30", "color": "#9b59b6", "category": "交流"},
    {"id": "p12", "title": "故事爸媽活動",                       "start": "2026-03-26",                  "color": "#2ecc71",  "category": "活動"},
    {"id": "p13", "title": "五年級英語活動",                      "start": "2026-03-26",                  "color": "#3498db",  "category": "活動", "description": "1:25-2:55 p.m., i/c玲"},
    {"id": "p14", "title": "Tales of Character: 五年級英文語常會活動", "start": "2026-03-26", "color": "#2ecc71", "category": "活動"},
    {"id": "p15", "title": "Tales of Character: 三年級英文語常會活動", "start": "2026-03-31", "color": "#2ecc71", "category": "活動"},
    {"id": "p16", "title": "學生春季生日會",                      "start": "2026-03-31",                  "color": "#e74c3c",  "category": "活動"},
    {"id": "p17", "title": "派發傑出學生選舉申請表",                "start": "2026-03-31",                  "color": "#7f8c8d",  "category": "校務"},
    {"id": "p18", "title": "領取正取生名單",                      "start": "2026-03-31",                  "color": "#7f8c8d",  "category": "校務"},
    {"id": "p19", "title": "復活節崇拜及小四福音活動",               "start": "2026-04-01",                  "color": "#e74c3c",  "category": "活動"},
    {"id": "p20", "title": "復活節假期",                         "start": "2026-04-02", "end": "2026-04-08", "color": "#e74c3c",  "category": "假期"},
    {"id": "p21", "title": "「新時代築夢計劃（人工智能）」交流團",     "start": "2026-04-03",                  "color": "#9b59b6",  "category": "交流"},
]

# ---------- 工具函數 ----------
def load_custom_events() -> list:
    if os.path.exists(EVENTS_FILE):
        try:
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_custom_events(events: list):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def get_color(category: str) -> str:
    return CATEGORY_COLORS.get(category, "#607d8b")


def parse_event_with_qwen(api_key: str, text: str, today: date) -> dict:
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    system_prompt = (
        f"你是一個學校校曆助手。今天是 {today.strftime('%Y年%m月%d日')}"
        f"（星期{weekdays[today.weekday()]}）。\n"
        "請從自然語言中提取事件信息，只返回純JSON（不要加markdown代碼塊），格式：\n"
        '{"title":"活動名稱","date":"YYYY-MM-DD","time":"HH:MM","end_date":"YYYY-MM-DD","description":""}\n'
        "time 和 end_date 可省略，date 必填。"
    )
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
    )
    content = response.choices[0].message.content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    return json.loads(content)


def build_calendar_events(all_events: list) -> list:
    result = []
    for ev in all_events:
        item = {
            "title": ev["title"],
            "start": ev["start"],
            "color": ev.get("color", "#607d8b"),
        }
        if ev.get("end"):
            item["end"] = ev["end"]
        if ev.get("description"):
            item["extendedProps"] = {"description": ev["description"]}
        result.append(item)
    return result


# ---------- 頁面設定 ----------
st.set_page_config(page_title="智慧校曆系統", page_icon="📅", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    .sync-badge {
        background:#27ae60;color:white;padding:3px 10px;
        border-radius:12px;font-size:0.85rem;vertical-align:middle;
    }
    .legend-dot {
        display:inline-block;width:12px;height:12px;
        border-radius:50%;margin-right:5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- 初始化 ----------
if "custom_events" not in st.session_state:
    st.session_state.custom_events = load_custom_events()
if "saved_api_key" not in st.session_state:
    st.session_state.saved_api_key = st.secrets.get("QWEN_API_KEY", "") if hasattr(st, "secrets") else ""

# ---------- 頁首 ----------
h_col1, h_col2 = st.columns([8, 2])
with h_col1:
    st.markdown("# 📅 智慧校曆系統")
with h_col2:
    st.markdown('<br><span class="sync-badge">✓ 即時同步中</span>', unsafe_allow_html=True)

# ==========================================
# 側邊欄
# ==========================================
with st.sidebar:
    st.header("⚙️ 設定與操作")

    # ── 1. API 金鑰 ──
    with st.expander("1. API 金鑰設定", expanded=not st.session_state.saved_api_key):
        st.markdown("[如何取得?](https://www.alibabacloud.com/en/product/model-studio)")
        key_input = st.text_input("Qwen API Key", type="password",
                                  value=st.session_state.saved_api_key,
                                  key="key_input")
        if st.button("儲存金鑰至瀏覽器", use_container_width=True):
            st.session_state.saved_api_key = key_input
            st.success("✅ 金鑰已儲存")
        if st.session_state.saved_api_key:
            st.success("✅ API 金鑰已設定")

    st.divider()

    # ── 2. 匯入現有校曆 ──
    with st.expander("2. 匯入現有校曆"):
        uploaded_json = st.file_uploader("上傳 JSON 校曆", type=["json"])
        if uploaded_json is not None:
            try:
                imported = json.loads(uploaded_json.read().decode("utf-8"))
                if isinstance(imported, list):
                    st.session_state.custom_events.extend(imported)
                    save_custom_events(st.session_state.custom_events)
                    st.success(f"✅ 已匯入 {len(imported)} 個活動")
                    st.rerun()
                else:
                    st.error("格式錯誤，需為 JSON 陣列")
            except Exception as e:
                st.error(f"匯入失敗：{e}")

    st.divider()

    # ── 3. 手動新增 ──
    with st.expander("3. 手動新增活動", expanded=True):
        with st.form("manual_form", clear_on_submit=True):
            new_title = st.text_input("活動名稱 *")
            new_date = st.date_input("日期", value=date.today())
            new_end = st.date_input("結束日期（可選）", value=None)
            new_cat = st.selectbox("分類", list(CATEGORY_COLORS.keys())[:-1])
            new_desc = st.text_area("備注", height=60)
            submitted = st.form_submit_button("直接新增", type="primary",
                                              use_container_width=True)
        if submitted:
            if not new_title:
                st.warning("請輸入活動名稱")
            else:
                ev = {
                    "id": f"c{datetime.now().timestamp():.0f}",
                    "title": new_title,
                    "start": str(new_date),
                    "color": get_color(new_cat),
                    "category": new_cat,
                    "description": new_desc,
                }
                if new_end and new_end > new_date:
                    ev["end"] = str(new_end + timedelta(days=1))
                st.session_state.custom_events.append(ev)
                save_custom_events(st.session_state.custom_events)
                st.success(f"✅ 已新增：{new_title}")
                st.rerun()

    st.divider()

    # ── 4. AI 智慧新增 ──
    with st.expander("4. AI 智慧新增", expanded=True):
        st.caption("例如：「下週三早上9點六年級家長會」")
        ai_text = st.text_area("自然語言輸入", height=80, label_visibility="collapsed",
                               placeholder="例如：下週三早上9點六年級家長會")
        ai_disabled = not st.session_state.saved_api_key or not HAS_OPENAI
        if st.button("送出給 Qwen 分析", type="primary",
                     use_container_width=True, disabled=ai_disabled):
            if ai_text.strip():
                with st.spinner("Qwen 分析中..."):
                    try:
                        result = parse_event_with_qwen(
                            st.session_state.saved_api_key, ai_text, date.today()
                        )
                        ev = {
                            "id": f"ai{datetime.now().timestamp():.0f}",
                            "title": result.get("title", ai_text),
                            "start": result.get("date", str(date.today())),
                            "color": get_color("AI新增"),
                            "category": "AI新增",
                            "description": result.get("description", ""),
                        }
                        if result.get("time"):
                            ev["start"] = f"{result['date']}T{result['time']}:00"
                        if result.get("end_date") and result["end_date"] != result.get("date"):
                            ev["end"] = result["end_date"]
                        st.session_state.custom_events.append(ev)
                        save_custom_events(st.session_state.custom_events)
                        st.success(f"✅ 已新增：{ev['title']}（{result.get('date', '')}）")
                        st.rerun()
                    except Exception as e:
                        st.error(f"解析失敗：{e}")
            else:
                st.warning("請輸入活動描述")
        if not st.session_state.saved_api_key:
            st.info("请先在「1. API 金鑰設定」填入金鑰")

    st.divider()

    # ── 匯出 ──
    st.subheader("📥 匯出校曆")
    export_data = json.dumps(st.session_state.custom_events, ensure_ascii=False, indent=2)
    st.download_button("下載自訂活動 JSON", data=export_data,
                       file_name="school_calendar.json", mime="application/json",
                       use_container_width=True)

# ==========================================
# 主要日曆區域
# ==========================================
all_events = PRELOADED_EVENTS + st.session_state.custom_events
calendar_events = build_calendar_events(all_events)

st.caption("💡 點擊空白可新增，點擊色塊看詳情")

if HAS_CALENDAR:
    calendar_options = {
        "initialView": "dayGridMonth",
        "locale": "zh-tw",
        "firstDay": 0,
        "initialDate": "2026-03-01",
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listWeek",
        },
        "buttonText": {
            "today": "今天",
            "month": "月",
            "week": "週",
            "list": "列表",
        },
        "height": 680,
        "selectable": True,
        "eventDisplay": "block",
    }

    cal_result = st_calendar(
        events=calendar_events,
        options=calendar_options,
        key="school_calendar",
    )

    # 點擊活動顯示詳情
    if cal_result and cal_result.get("eventClick"):
        ev_info = cal_result["eventClick"]["event"]
        with st.container():
            st.markdown("---")
            st.subheader(f"📌 {ev_info['title']}")
            cols = st.columns(2)
            cols[0].write(f"**開始：** {ev_info.get('start', '')[:10]}")
            if ev_info.get("end"):
                cols[1].write(f"**結束：** {ev_info['end'][:10]}")
            desc = (ev_info.get("extendedProps") or {}).get("description", "")
            if desc:
                st.write(f"**備注：** {desc}")

    # 點擊日期提示
    if cal_result and cal_result.get("dateClick"):
        clicked_date = cal_result["dateClick"]["date"][:10]
        st.info(f"📆 已選擇 {clicked_date}，請使用左側「手動新增活動」欄位新增事件")

else:
    st.warning("請安裝 streamlit-calendar：`pip install streamlit-calendar`")
    st.markdown("#### 活動列表（備用模式）")
    events_by_date: dict = defaultdict(list)
    for ev in all_events:
        events_by_date[ev["start"][:10]].append(ev["title"])
    rows = [{"日期": d, "活動": " / ".join(events_by_date[d])}
            for d in sorted(events_by_date)]
    st.dataframe(rows, use_container_width=True)

# ==========================================
# 圖例
# ==========================================
st.markdown("---")
legend_html = " &nbsp; ".join(
    f'<span class="legend-dot" style="background:{c}"></span>{cat}'
    for cat, c in CATEGORY_COLORS.items()
)
st.markdown(f"<small>{legend_html}</small>", unsafe_allow_html=True)

# ==========================================
# 管理自訂活動
# ==========================================
if st.session_state.custom_events:
    with st.expander(f"🗂️ 管理自訂活動（共 {len(st.session_state.custom_events)} 項）"):
        for i, ev in enumerate(st.session_state.custom_events):
            c1, c2, c3, c4 = st.columns([3, 2, 1, 0.6])
            c1.write(ev["title"])
            c2.write(ev["start"][:10])
            c3.write(ev.get("category", ""))
            if c4.button("🗑️", key=f"del_{i}", help=f"刪除 {ev['title']}"):
                st.session_state.custom_events.pop(i)
                save_custom_events(st.session_state.custom_events)
                st.rerun()
