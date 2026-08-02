from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
UPLOAD_DIR = ROOT / "uploads"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

FILES = {
    "todos": DATA_DIR / "todos.json",
    "students": DATA_DIR / "students.json",
    "health": DATA_DIR / "health.json",
    "left_behind": DATA_DIR / "left_behind.json",
    "special_focus": DATA_DIR / "special_focus.json",
    "discipline": DATA_DIR / "discipline.json",
    "timetable": DATA_DIR / "timetable.json",
    "safety": DATA_DIR / "safety.json",
    "scores": DATA_DIR / "scores.json",
    "homework": DATA_DIR / "homework.json",
    "personal": DATA_DIR / "personal.json",
}

NAV_ITEMS = {
    "今日概览": "⌂",
    "待办事项": "✓",
    "学生档案": "♧",
    "班级课表": "▦",
    "教学记录": "✎",
}


def load(name: str) -> list[dict]:
    path = FILES[name]
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save(name: str, rows: list[dict]) -> None:
    FILES[name].write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def add_record(name: str, record: dict) -> None:
    rows = load(name)
    rows.insert(0, {"id": uuid.uuid4().hex, "created_at": datetime.now().isoformat(timespec="seconds"), **record})
    save(name, rows)


def save_upload(uploaded_file, folder: str) -> str | None:
    if uploaded_file is None:
        return None
    target_dir = UPLOAD_DIR / folder
    target_dir.mkdir(exist_ok=True)
    safe_name = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}_{Path(uploaded_file.name).name}"
    target = target_dir / safe_name
    target.write_bytes(uploaded_file.getbuffer())
    return str(target.relative_to(ROOT))


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Serif+SC:wght@500;600;700&display=swap');
        :root { --ink:#1f2a24; --muted:#68746c; --paper:#f7f5ef; --card:#fffdf8; --line:#e6e2d8; --accent:#2f6b52; --accent-soft:#e5f0e9; --warning:#a56828; }
        .stApp { background:var(--paper); color:var(--ink); }
        [data-testid="stSidebar"] { background:#ecefe8; border-right:1px solid var(--line); }
        [data-testid="stSidebar"] h1 { font-family:'Noto Serif SC', serif; color:var(--ink); letter-spacing:-.04em; }
        h1,h2,h3 { font-family:'Noto Serif SC', serif !important; color:var(--ink) !important; letter-spacing:-.025em; }
        p, label, div, button { font-family:'DM Sans','Microsoft Yahei',sans-serif; }
        .eyebrow { color:var(--accent); font-size:.73rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.35rem; }
        .hero { padding:1.15rem 0 .7rem; border-bottom:1px solid var(--line); margin-bottom:1.1rem; }
        .hero h1 { font-size:2.3rem; margin:0; }
        .hero p { color:var(--muted); margin:.25rem 0 0; }
        .metric { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; min-height:100px; }
        .metric .label { color:var(--muted); font-size:.82rem; }
        .metric .value { color:var(--ink); font-size:2rem; font-weight:700; line-height:1.15; margin-top:.35rem; }
        .metric .note { color:var(--accent); font-size:.8rem; margin-top:.35rem; }
        .section { border-top:1px solid var(--line); padding-top:1rem; margin-top:1.25rem; }
        .quick { background:var(--accent-soft); border:1px solid #cbded2; border-radius:14px; padding:.8rem 1rem; }
        .quick-title { color:var(--accent); font-weight:700; margin-bottom:.2rem; }
        .tag { display:inline-block; padding:.22rem .5rem; border-radius:999px; font-size:.73rem; background:var(--accent-soft); color:var(--accent); }
        .tag-warn { background:#f7ead8; color:var(--warning); }
        .stButton > button { border-radius:10px; border:1px solid #cbd7ce; color:var(--accent); background:var(--card); }
        .stButton > button:hover { border-color:var(--accent); color:var(--accent); }
        .stButton > button[kind="primary"] { background:var(--accent); color:#fff; border-color:var(--accent); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric(label: str, value: str | int, note: str) -> None:
    st.markdown(f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div><div class="note">{note}</div></div>', unsafe_allow_html=True)


def section_heading(eyebrow: str, title: str) -> None:
    st.markdown(f'<div class="section"><div class="eyebrow">{eyebrow}</div><h3>{title}</h3></div>', unsafe_allow_html=True)


def page_home() -> None:
    todos = load("todos")
    students = load("students")
    homework = load("homework")
    today = date.today().isoformat()
    pending = [x for x in todos if x.get("status") != "已完成"]
    due_today = [x for x in pending if x.get("due_date") == today]
    unfinished = sum(int(x.get("未完成次数", x.get("unfinished", 0)) or 0) for x in homework)
    st.markdown('<div class="hero"><div class="eyebrow">Teacher desk / 个人工作台</div><h1>今天，先照看最重要的事。</h1><p>班级事务、语文教学与学生成长记录，放在一个安静可靠的地方。</p></div>', unsafe_allow_html=True)
    cols = st.columns(4)
    cards = [("待办事项", len(pending), f"今日到期 {len(due_today)} 项"), ("学生档案", len(students), "持续更新中"), ("作业未完成", unfinished, "累计登记次数"), ("工作日", date.today().strftime("%m月%d日"), date.today().strftime("%A"))]
    for col, args in zip(cols, cards):
        with col:
            metric(*args)
    section_heading("Focus", "接下来要做什么")
    if pending:
        for item in pending[:5]:
            c1, c2, c3 = st.columns([5, 2, 1])
            c1.write(f"**{item.get('title', '未命名事项')}**  ·  {item.get('category', '日常')}" )
            c2.caption(item.get("due_date", "未设置日期"))
            if c3.button("完成", key=f"home_done_{item['id']}"):
                rows = load("todos")
                for row in rows:
                    if row["id"] == item["id"]:
                        row["status"] = "已完成"
                save("todos", rows)
                st.rerun()
    else:
        st.info("还没有待办。去左侧“待办事项”添加今天的第一件事。")
    st.markdown('<div class="quick"><div class="quick-title">⌁ 快速入口</div><span class="small">从左侧导航进入模块，录入资料后会自动保存到本机 data 文件夹。</span></div>', unsafe_allow_html=True)


def page_todos() -> None:
    st.title("✓ 待办事项")
    with st.form("todo_form", clear_on_submit=True):
        c1, c2 = st.columns([3, 1])
        title = c1.text_input("事项名称", placeholder="例如：完成周一安全教育留痕")
        category = c2.selectbox("类型", ["班主任", "语文教学", "家校沟通", "其他"])
        c3, c4, c5 = st.columns(3)
        due = c3.date_input("完成日期", value=date.today())
        remind = c4.selectbox("提醒", ["不提醒", "当天 08:00", "提前 30 分钟", "提前 1 天"])
        repeat = c5.selectbox("重复", ["不重复", "每天", "每周"])
        note = st.text_area("备注", height=80)
        if st.form_submit_button("添加待办", type="primary") and title.strip():
            add_record("todos", {"title": title.strip(), "category": category, "due_date": due.isoformat(), "remind": remind, "repeat": repeat, "note": note, "status": "待完成"})
            st.success("已添加")
    rows = load("todos")
    section_heading("List", "全部事项")
    for item in rows:
        status = item.get("status", "待完成")
        c1, c2, c3 = st.columns([5, 2, 1])
        mark = "~~" if status == "已完成" else ""
        c1.write(f"{mark}**{item.get('title')}**{mark}  ·  {item.get('category')}")
        c2.caption(f"{item.get('due_date')} / {item.get('remind', '不提醒')}")
        if status != "已完成" and c3.button("完成", key=f"todo_{item['id']}"):
            for row in rows:
                if row["id"] == item["id"]:
                    row["status"] = "已完成"
            save("todos", rows)
            st.rerun()


def page_students() -> None:
    st.title("♧ 学生档案")
    tabs = st.tabs(["名册", "健康关注", "留守儿童", "特殊关注", "违纪记录"])
    with tabs[0]:
        with st.form("student_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("姓名")
            class_name = c2.text_input("班级", placeholder="七年级 3 班")
            student_no = c3.text_input("学号")
            contact = st.text_input("家长联系方式")
            if st.form_submit_button("添加学生", type="primary") and name.strip():
                add_record("students", {"name": name.strip(), "class_name": class_name, "student_no": student_no, "contact": contact})
                st.success("学生已加入名册")
        rows = load("students")
        cols = ["name", "class_name", "student_no", "contact"]
        st.dataframe(pd.DataFrame(rows)[cols] if rows else pd.DataFrame(columns=cols), use_container_width=True, hide_index=True)
    for tab, kind, title in zip(tabs[1:], ["特异体质", "留守儿童", "特殊关注", "违纪记录"], ["特异体质记录", "留守儿童记录", "特殊关注记录", "违纪行为处理"]):
        with tab:
            st.subheader(title)
            students = [x.get("name") for x in load("students")]
            with st.form(f"record_{kind}", clear_on_submit=True):
                student = st.selectbox("关联学生", students or ["请先添加学生"])
                detail = st.text_area("记录内容", placeholder="写下事实、措施、反馈或后续跟进…")
                uploaded = st.file_uploader("上传截图或照片（可选）", type=["png", "jpg", "jpeg", "pdf"], key=f"upload_{kind}")
                if st.form_submit_button("保存记录", type="primary") and student != "请先添加学生" and detail.strip():
                    path = save_upload(uploaded, kind_name(kind))
                    add_record(kind_name(kind), {"student": student, "detail": detail, "attachment": path, "record_date": date.today().isoformat()})
                    st.success("记录已保存")
            rows = load(kind_name(kind))
            for row in rows[:10]:
                st.write(f"**{row.get('student')}** · {row.get('record_date')}")
                st.caption(row.get("detail"))
                if row.get("attachment"):
                    st.caption(f"附件：{row['attachment']}")


def kind_name(kind: str) -> str:
    return {"特异体质": "health", "留守儿童": "left_behind", "特殊关注": "special_focus", "违纪记录": "discipline"}[kind]


def page_timetable() -> None:
    st.title("▦ 班级课表")
    with st.form("schedule_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        day = c1.selectbox("星期", ["周一", "周二", "周三", "周四", "周五"])
        period = c2.text_input("节次", placeholder="第 1 节")
        class_name = c3.text_input("班级")
        subject = st.text_input("课程", value="语文")
        reminder = st.checkbox("加入课前提醒", value=True)
        if st.form_submit_button("保存课表", type="primary") and period and class_name:
            add_record("timetable", {"day": day, "period": period, "class_name": class_name, "subject": subject, "reminder": reminder})
            st.success("已保存")
    rows = load("timetable")
    cols = ["day", "period", "class_name", "subject", "reminder"]
    st.dataframe(pd.DataFrame(rows)[cols] if rows else pd.DataFrame(columns=cols), use_container_width=True, hide_index=True)


def page_records() -> None:
    st.title("✎ 教学记录")
    tabs = st.tabs(["安全教育", "成绩分析", "作业情况", "个人成果"])
    with tabs[0]:
        record_form("safety", "安全教育留痕", ["主题", "教育形式", "内容摘要"])
    with tabs[1]:
        st.subheader("成绩导入")
        uploaded = st.file_uploader("上传 Excel 或 CSV", type=["xlsx", "xls", "csv"])
        if uploaded:
            try:
                df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
                st.dataframe(df.head(20), use_container_width=True, hide_index=True)
                st.caption("当前为预览模式，确认后可将表格保存至本地成绩记录。")
            except Exception as exc:
                st.error(f"无法读取文件：{exc}")
    with tabs[2]:
        record_form("homework", "作业登记", ["作业名称", "班级", "未完成次数"])
    with tabs[3]:
        record_form("personal", "个人成果", ["成果名称", "类别", "时间"])


def record_form(name: str, title: str, fields: list[str]) -> None:
    st.subheader(title)
    with st.form(f"form_{name}", clear_on_submit=True):
        values = {field: st.text_input(field) for field in fields}
        uploaded = st.file_uploader("上传附件（可选）", type=["png", "jpg", "jpeg", "pdf", "ppt", "pptx", "doc", "docx"], key=f"file_{name}")
        values["detail"] = st.text_area("备注", height=80)
        if st.form_submit_button("保存记录", type="primary"):
            values["attachment"] = save_upload(uploaded, name)
            add_record(name, values)
            st.success("已保存到本地")
    rows = load(name)
    if rows:
        st.dataframe(pd.DataFrame(rows).drop(columns=["id", "created_at"], errors="ignore"), use_container_width=True, hide_index=True)


st.set_page_config(page_title="教师工作台", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
inject_css()
with st.sidebar:
    st.markdown("# 教师工作台")
    st.caption("班主任 · 语文教师")
    st.divider()
    options = [f"{icon}  {label}" for label, icon in NAV_ITEMS.items()]
    selected = st.radio("导航", options, label_visibility="collapsed")
    page = selected.split("  ", 1)[1]
    st.divider()
    st.caption(f"本地模式 · {date.today():%Y-%m-%d}")

if page == "今日概览":
    page_home()
elif page == "待办事项":
    page_todos()
elif page == "学生档案":
    page_students()
elif page == "班级课表":
    page_timetable()
else:
    page_records()
