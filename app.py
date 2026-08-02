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

NAV_ITEMS = {"今日概览": "⌂", "待办事项": "✓", "学生档案": "♧", "班级课表": "▦", "教学记录": "✎"}


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


def add_record(name: str, record: dict) -> str:
    record_id = uuid.uuid4().hex
    rows = load(name)
    rows.insert(0, {"id": record_id, "created_at": datetime.now().isoformat(timespec="seconds"), **record})
    save(name, rows)
    return record_id


def update_record(name: str, record_id: str, patch: dict) -> bool:
    rows = load(name)
    for row in rows:
        if row.get("id") == record_id:
            row.update(patch)
            row["updated_at"] = datetime.now().isoformat(timespec="seconds")
            save(name, rows)
            return True
    return False


def delete_record(name: str, record_id: str) -> bool:
    rows = load(name)
    new_rows = [row for row in rows if row.get("id") != record_id]
    if len(new_rows) == len(rows):
        return False
    save(name, new_rows)
    return True


def save_upload(uploaded_file, folder: str) -> str | None:
    if uploaded_file is None:
        return None
    target_dir = UPLOAD_DIR / folder
    target_dir.mkdir(exist_ok=True)
    safe_name = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}_{Path(uploaded_file.name).name}"
    target = target_dir / safe_name
    target.write_bytes(uploaded_file.getbuffer())
    return str(target.relative_to(ROOT))


def text_match(row: dict, query: str) -> bool:
    if not query.strip():
        return True
    return query.strip().lower() in " ".join(str(value) for value in row.values()).lower()


def safe_date(value: str | None) -> date:
    try:
        return date.fromisoformat(value) if value else date.today()
    except (TypeError, ValueError):
        return date.today()


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Serif+SC:wght@500;600;700&display=swap');
        :root { --ink:#1f2a24; --muted:#68746c; --paper:#f7f5ef; --card:#fffdf8; --line:#e6e2d8; --accent:#2f6b52; --accent-soft:#e5f0e9; }
        .stApp { background:var(--paper); color:var(--ink); }
        [data-testid="stSidebar"] { background:#ecefe8; border-right:1px solid var(--line); }
        [data-testid="stSidebar"] h1, h1, h2, h3 { font-family:'Noto Serif SC', serif !important; color:var(--ink) !important; letter-spacing:-.025em; }
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
        .small { color:var(--muted); font-size:.88rem; }
        .record-title { font-weight:600; color:var(--ink); padding-top:.45rem; }
        .record-meta { color:var(--muted); font-size:.86rem; padding-top:.45rem; }
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


def preview_table(rows: list[dict], columns: list[tuple[str, str]]) -> None:
    """Keep the complete read-only preview visible above row-level actions."""
    data = [{label: row.get(key, "") for key, label in columns} for row in rows]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


def row_actions(row: dict, title: str, meta: str, name: str, edit_fn) -> None:
    left, middle, edit_col, delete_col = st.columns([5, 2, 1, 1])
    left.markdown(f'<div class="record-title">{title}</div>', unsafe_allow_html=True)
    middle.markdown(f'<div class="record-meta">{meta}</div>', unsafe_allow_html=True)
    if edit_col.button("编辑", key=f"edit_{name}_{row['id']}"):
        edit_fn(row)
    if delete_col.button("删除", key=f"delete_{name}_{row['id']}"):
        delete_dialog(name, row["id"], title)


@st.dialog("确认删除")
def delete_dialog(name: str, record_id: str, label: str) -> None:
    st.warning(f"确定要删除“{label}”吗？删除后无法从工作台恢复。")
    yes, no = st.columns(2)
    if yes.button("确认删除", key=f"confirm_{name}_{record_id}", type="primary"):
        delete_record(name, record_id)
        st.rerun()
    if no.button("取消", key=f"cancel_{name}_{record_id}"):
        st.rerun()


@st.dialog("编辑待办")
def edit_todo_dialog(item: dict) -> None:
    categories = ["班主任", "语文教学", "家校沟通", "其他"]
    reminders = ["不提醒", "当天 08:00", "提前 30 分钟", "提前 1 天"]
    with st.form(f"dialog_todo_{item['id']}"):
        title = st.text_input("事项名称", value=item.get("title", ""))
        category = st.selectbox("类型", categories, index=categories.index(item.get("category")) if item.get("category") in categories else 0)
        due = st.date_input("完成日期", value=safe_date(item.get("due_date")))
        remind = st.selectbox("提醒", reminders, index=reminders.index(item.get("remind")) if item.get("remind") in reminders else 0)
        status = st.selectbox("状态", ["待完成", "已完成"], index=1 if item.get("status") == "已完成" else 0)
        note = st.text_area("备注", value=item.get("note", ""))
        if st.form_submit_button("保存修改", type="primary"):
            if not title.strip():
                st.error("事项名称不能为空")
            else:
                update_record("todos", item["id"], {"title": title.strip(), "category": category, "due_date": due.isoformat(), "remind": remind, "status": status, "note": note})
                st.rerun()


@st.dialog("编辑学生")
def edit_student_dialog(item: dict) -> None:
    with st.form(f"dialog_student_{item['id']}"):
        name = st.text_input("姓名", value=item.get("name", ""))
        class_name = st.text_input("班级", value=item.get("class_name", ""))
        student_no = st.text_input("学号", value=item.get("student_no", ""))
        contact = st.text_input("家长联系方式", value=item.get("contact", ""))
        if st.form_submit_button("保存修改", type="primary"):
            if not name.strip():
                st.error("姓名不能为空")
            else:
                update_record("students", item["id"], {"name": name.strip(), "class_name": class_name, "student_no": student_no, "contact": contact})
                st.rerun()


@st.dialog("编辑学生记录")
def edit_student_record_dialog(name: str, item: dict) -> None:
    students = [x.get("name") for x in load("students")]
    with st.form(f"dialog_record_{name}_{item['id']}"):
        student = st.selectbox("关联学生", students or [item.get("student", "")], index=students.index(item.get("student")) if item.get("student") in students else 0)
        detail = st.text_area("记录内容", value=item.get("detail", ""))
        record_date = st.date_input("记录日期", value=safe_date(item.get("record_date")))
        if st.form_submit_button("保存修改", type="primary"):
            update_record(name, item["id"], {"student": student, "detail": detail.strip(), "record_date": record_date.isoformat()})
            st.rerun()


@st.dialog("编辑课表")
def edit_timetable_dialog(item: dict) -> None:
    days = ["周一", "周二", "周三", "周四", "周五"]
    with st.form(f"dialog_timetable_{item['id']}"):
        day = st.selectbox("星期", days, index=days.index(item.get("day")) if item.get("day") in days else 0)
        period = st.text_input("节次", value=item.get("period", ""))
        class_name = st.text_input("班级", value=item.get("class_name", ""))
        subject = st.text_input("课程", value=item.get("subject", "语文"))
        reminder = st.checkbox("加入课前提醒", value=bool(item.get("reminder", True)))
        if st.form_submit_button("保存修改", type="primary"):
            update_record("timetable", item["id"], {"day": day, "period": period.strip(), "class_name": class_name.strip(), "subject": subject.strip(), "reminder": reminder})
            st.rerun()


@st.dialog("编辑教学记录")
def edit_generic_dialog(name: str, fields: list[str], item: dict) -> None:
    with st.form(f"dialog_generic_{name}_{item['id']}"):
        patch = {field: st.text_input(field, value=str(item.get(field, ""))) for field in fields}
        patch["detail"] = st.text_area("备注", value=item.get("detail", ""))
        if st.form_submit_button("保存修改", type="primary"):
            if any(not str(patch[field]).strip() for field in fields):
                st.error("请完整填写带标签的字段")
            else:
                update_record(name, item["id"], patch)
                st.rerun()


@st.dialog("编辑成绩记录")
def edit_score_dialog(item: dict) -> None:
    with st.form(f"dialog_score_{item['id']}"):
        name = st.text_input("考试名称", value=item.get("name", ""))
        if st.form_submit_button("保存修改", type="primary"):
            update_record("scores", item["id"], {"name": name.strip()})
            st.rerun()


def page_home() -> None:
    todos, students, homework = load("todos"), load("students"), load("homework")
    today = date.today().isoformat()
    pending = [x for x in todos if x.get("status") != "已完成"]
    due_today = [x for x in pending if x.get("due_date") == today]
    unfinished = sum(int(x.get("未完成次数", x.get("unfinished", 0)) or 0) for x in homework)
    st.markdown('<div class="hero"><div class="eyebrow">Teacher desk / 个人工作台</div><h1>今天，先照看最重要的事。</h1><p>班级事务、语文教学与学生成长记录，放在一个安静可靠的地方。</p></div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for col, args in zip(cols, [("待办事项", len(pending), f"今日到期 {len(due_today)} 项"), ("学生档案", len(students), "持续更新中"), ("作业未完成", unfinished, "累计登记次数"), ("工作日", date.today().strftime("%m月%d日"), date.today().strftime("%A"))]):
        with col:
            metric(*args)
    section_heading("Focus", "接下来要做什么")
    if pending:
        for item in pending[:5]:
            c1, c2, c3 = st.columns([5, 2, 1])
            c1.write(f"**{item.get('title', '未命名事项')}**  ·  {item.get('category', '日常')}")
            c2.caption(item.get("due_date", "未设置日期"))
            if c3.button("完成", key=f"home_done_{item['id']}"):
                update_record("todos", item["id"], {"status": "已完成"})
                st.rerun()
    else:
        st.info("还没有待办。去左侧“待办事项”添加今天的第一件事。")
    st.markdown('<div class="quick"><div class="quick-title">⌁ 快速入口</div><span class="small">所有模块都支持完整预览、编辑和删除，资料会保存到本机 data 文件夹。</span></div>', unsafe_allow_html=True)


def page_todos() -> None:
    st.title("✓ 待办事项")
    with st.form("todo_form", clear_on_submit=True):
        c1, c2 = st.columns([3, 1])
        title = c1.text_input("事项名称", placeholder="例如：完成周一安全教育留痕")
        category = c2.selectbox("类型", ["班主任", "语文教学", "家校沟通", "其他"])
        due = st.date_input("完成日期", value=date.today())
        remind = st.selectbox("提醒", ["不提醒", "当天 08:00", "提前 30 分钟", "提前 1 天"])
        repeat = st.selectbox("重复", ["不重复", "每天", "每周"])
        note = st.text_area("备注", height=80)
        if st.form_submit_button("添加待办", type="primary"):
            if title.strip():
                add_record("todos", {"title": title.strip(), "category": category, "due_date": due.isoformat(), "remind": remind, "repeat": repeat, "note": note, "status": "待完成"})
                st.success("已添加")
            else:
                st.error("请填写事项名称")
    section_heading("Search", "预览与管理")
    q1, q2 = st.columns([3, 1])
    query = q1.text_input("关键词", placeholder="搜索事项、类型或备注", key="todo_query")
    status_filter = q2.selectbox("状态", ["全部", "待完成", "已完成"], key="todo_status")
    rows = [row for row in load("todos") if text_match(row, query) and (status_filter == "全部" or row.get("status") == status_filter)]
    preview_table(rows, [("title", "事项"), ("category", "类型"), ("due_date", "截止日期"), ("status", "状态"), ("remind", "提醒")])
    st.caption(f"显示 {len(rows)} / {len(load('todos'))} 条记录")
    for item in rows:
        row_actions(item, item.get("title", "未命名事项"), f"{item.get('due_date', '')} · {item.get('status', '待完成')}", "todo", edit_todo_dialog)


def page_students() -> None:
    st.title("♧ 学生档案")
    tabs = st.tabs(["名册", "特异体质", "留守儿童", "特殊关注", "违纪记录"])
    with tabs[0]:
        with st.form("student_form", clear_on_submit=True):
            name = st.text_input("姓名")
            class_name = st.text_input("班级", placeholder="七年级 3 班")
            student_no = st.text_input("学号")
            contact = st.text_input("家长联系方式")
            if st.form_submit_button("添加学生", type="primary"):
                if name.strip():
                    add_record("students", {"name": name.strip(), "class_name": class_name, "student_no": student_no, "contact": contact})
                    st.success("学生已加入名册")
                else:
                    st.error("请填写学生姓名")
        section_heading("Search", "预览与管理")
        query = st.text_input("关键词", placeholder="搜索姓名、班级、学号或联系方式", key="student_query")
        rows = [row for row in load("students") if text_match(row, query)]
        preview_table(rows, [("name", "姓名"), ("class_name", "班级"), ("student_no", "学号"), ("contact", "家长联系方式")])
        st.caption(f"显示 {len(rows)} / {len(load('students'))} 名学生")
        for item in rows:
            row_actions(item, item.get("name", "未命名"), f"{item.get('class_name', '未分班')} · {item.get('student_no', '')}", "student", edit_student_dialog)
    for tab, name, title in zip(tabs[1:], ["health", "left_behind", "special_focus", "discipline"], ["特异体质记录", "留守儿童记录", "特殊关注记录", "违纪行为处理"]):
        with tab:
            student_record_page(name, title)


def student_record_page(name: str, title: str) -> None:
    st.subheader(title)
    students = [x.get("name") for x in load("students")]
    with st.form(f"record_form_{name}", clear_on_submit=True):
        student = st.selectbox("关联学生", students or ["请先添加学生"])
        detail = st.text_area("记录内容", placeholder="写下事实、措施、反馈或后续跟进…")
        uploaded = st.file_uploader("上传截图或照片（可选）", type=["png", "jpg", "jpeg", "pdf"], key=f"upload_{name}")
        if st.form_submit_button("保存记录", type="primary"):
            if student == "请先添加学生" or not detail.strip():
                st.error("请选择学生并填写记录内容")
            else:
                add_record(name, {"student": student, "detail": detail.strip(), "attachment": save_upload(uploaded, name), "record_date": date.today().isoformat()})
                st.success("记录已保存")
    section_heading("Search", "预览与管理")
    query = st.text_input("关键词", placeholder="搜索学生姓名或记录内容", key=f"query_{name}")
    rows = [row for row in load(name) if text_match(row, query)]
    preview_table(rows, [("student", "学生"), ("record_date", "日期"), ("detail", "记录内容"), ("attachment", "附件")])
    st.caption(f"显示 {len(rows)} 条记录")
    for item in rows:
        row_actions(item, item.get("student", "未关联"), f"{item.get('record_date', '')} · {str(item.get('detail', ''))[:35]}", name, lambda record: edit_student_record_dialog(name, record))


def page_timetable() -> None:
    st.title("▦ 班级课表")
    with st.form("schedule_form", clear_on_submit=True):
        day = st.selectbox("星期", ["周一", "周二", "周三", "周四", "周五"])
        period = st.text_input("节次", placeholder="第 1 节")
        class_name = st.text_input("班级")
        subject = st.text_input("课程", value="语文")
        reminder = st.checkbox("加入课前提醒", value=True)
        if st.form_submit_button("保存课表", type="primary"):
            if period.strip() and class_name.strip():
                add_record("timetable", {"day": day, "period": period.strip(), "class_name": class_name.strip(), "subject": subject.strip(), "reminder": reminder})
                st.success("已保存")
            else:
                st.error("请填写节次和班级")
    section_heading("Search", "预览与管理")
    query = st.text_input("关键词", placeholder="搜索星期、班级或课程", key="timetable_query")
    rows = [row for row in load("timetable") if text_match(row, query)]
    preview_table(rows, [("day", "星期"), ("period", "节次"), ("class_name", "班级"), ("subject", "课程"), ("reminder", "课前提醒")])
    for item in rows:
        row_actions(item, f"{item.get('day')} · {item.get('period')}", f"{item.get('class_name')} · {item.get('subject')}", "timetable", edit_timetable_dialog)


def page_records() -> None:
    st.title("✎ 教学记录")
    tabs = st.tabs(["安全教育", "成绩分析", "作业情况", "个人成果"])
    with tabs[0]:
        record_form("safety", "安全教育留痕", ["主题", "教育形式", "内容摘要"], ["png", "jpg", "jpeg", "pdf"])
    with tabs[1]:
        score_page()
    with tabs[2]:
        record_form("homework", "作业登记", ["作业名称", "班级", "未完成次数"], ["png", "jpg", "jpeg", "pdf"])
    with tabs[3]:
        record_form("personal", "个人成果", ["成果名称", "类别", "时间"], ["png", "jpg", "jpeg", "pdf", "ppt", "pptx", "doc", "docx"])


def record_form(name: str, title: str, fields: list[str], upload_types: list[str]) -> None:
    st.subheader(title)
    with st.form(f"form_{name}", clear_on_submit=True):
        values = {field: st.text_input(field) for field in fields}
        uploaded = st.file_uploader("上传附件（可选）", type=upload_types, key=f"file_{name}")
        values["detail"] = st.text_area("备注", height=80)
        if st.form_submit_button("保存记录", type="primary"):
            if any(not str(values[field]).strip() for field in fields):
                st.error("请完整填写带标签的字段")
            else:
                values["attachment"] = save_upload(uploaded, name)
                add_record(name, values)
                st.success("已保存到本地")
    section_heading("Search", "预览与管理")
    query = st.text_input("关键词", placeholder="搜索记录内容", key=f"query_{name}")
    rows = [row for row in load(name) if text_match(row, query)]
    preview_table(rows, [(field, field) for field in fields] + [("detail", "备注"), ("attachment", "附件")])
    st.caption(f"显示 {len(rows)} 条记录")
    for item in rows:
        label = next((str(item.get(field)) for field in fields if item.get(field)), "未命名记录")
        row_actions(item, label, str(item.get("created_at", ""))[:10], name, lambda record: edit_generic_dialog(name, fields, record))


def score_page() -> None:
    st.subheader("成绩导入与管理")
    uploaded = st.file_uploader("上传 Excel 或 CSV", type=["xlsx", "xls", "csv"], key="score_upload")
    if uploaded:
        try:
            df = pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)
            st.dataframe(df, use_container_width=True, hide_index=True)
            score_name = st.text_input("本次考试名称", value=Path(uploaded.name).stem, key="score_name")
            if st.button("确认保存成绩", type="primary"):
                add_record("scores", {"name": score_name.strip() or Path(uploaded.name).stem, "filename": uploaded.name, "attachment": save_upload(uploaded, "scores"), "columns": list(df.columns), "rows": df.to_dict(orient="records"), "import_date": date.today().isoformat()})
                st.success("成绩文件已保存")
                st.rerun()
        except Exception as exc:
            st.error(f"无法读取文件：{exc}")
    section_heading("Search", "预览与管理")
    query = st.text_input("关键词", placeholder="搜索考试名称或文件名", key="score_query")
    rows = [row for row in load("scores") if text_match(row, query)]
    preview_table(rows, [("name", "考试名称"), ("filename", "文件"), ("import_date", "导入日期")])
    st.caption(f"显示 {len(rows)} 份成绩文件")
    for item in rows:
        row_actions(item, item.get("name", "未命名考试"), f"{item.get('import_date', '')} · {len(item.get('rows', []))} 行", "score", edit_score_dialog)


st.set_page_config(page_title="教师工作台", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
inject_css()
with st.sidebar:
    st.markdown("# 教师工作台")
    st.caption("班主任 · 语文教师")
    st.divider()
    selected = st.radio("导航", [f"{icon}  {label}" for label, icon in NAV_ITEMS.items()], label_visibility="collapsed")
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
