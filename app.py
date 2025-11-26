import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import requests # Imported at top level for safety

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="FinTrack Sync", page_icon="📈", layout="wide")

# --- SECURITY: LOAD SLACK URL ---
if "SLACK_WEBHOOK_URL" in st.secrets:
    SLACK_WEBHOOK_URL = st.secrets["SLACK_WEBHOOK_URL"]
else:
    SLACK_WEBHOOK_URL = "hooks.slack.com/services/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"

# --- TEAM CONFIGURATION ---
TEAM = ["All", "Kathy", "Tony", "Karim", "Agnis", "Thomas"]

# PASTE REAL SLACK MEMBER IDs HERE
TEAM_SLACK_IDS = {
    "Kathy": "U05AS678C8Y",
    "Tony": "U057DMZKK0C",
    "Karim": "U07TJM3404D",
    "Agnis": "U02BT9GEB8B",
    "Thomas": "U06CVDPFAPK"
}

# --- CATEGORIES ---
CATEGORIES = [
    "💸 Daily Funding (12PM)",
    "💳 ACH Request",
    "🧾 Weekly Vendor Payment",
    "📊 Budget & Forecast",
    "🤝 Revenue Share",
    "🏦 ATB Reporting",
    "🔄 SOFR Renewal",
    "🔐 GIC"
]

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    h1, h2, h3, p { font-family: 'Inter', sans-serif; }
    .finance-banner {
        background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        display: flex; align-items: center; justify-content: space-between;
    }
    div[data-testid="column"] { background-color: transparent; }
    .category-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px; transition: transform 0.2s;
    }
    .urgent-card { border-top: 5px solid #e11d48; }
    .normal-card { border-top: 5px solid #6366f1; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    
    /* Make the Archive button stand out */
    div.stButton > button:first-child {
        border-radius: 8px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA SETUP ---

def get_future_date(days=0, hours=0):
    return datetime.now() + timedelta(days=days, hours=hours)

if 'tasks' not in st.session_state:
    st.session_state.tasks = pd.DataFrame([
        {"Task": "Approve Wire Transfers", "Category": "💸 Daily Funding (12PM)", "Assignee": TEAM[1], "Due Date": get_future_date(hours=1), "Status": False, "Urgent": True},
        {"Task": "Process Vendor Invoices", "Category": "🧾 Weekly Vendor Payment", "Assignee": TEAM[2], "Due Date": get_future_date(days=0, hours=5), "Status": False, "Urgent": False},
        {"Task": "Submit Compliance Doc", "Category": "🏦 ATB Reporting", "Assignee": TEAM[3], "Due Date": get_future_date(days=1, hours=-2), "Status": False, "Urgent": False},
    ])

if 'archived' not in st.session_state:
    st.session_state.archived = pd.DataFrame(columns=["Task", "Category", "Assignee", "Due Date", "Status", "Urgent", "Completed At"])

# --- 3. HELPER FUNCTIONS ---

def get_slack_tag(name):
    """Helper to convert name to Slack ID tag"""
    if name in TEAM_SLACK_IDS:
        return f"<@{TEAM_SLACK_IDS[name]}>"
    return name

def send_slack_notification(task, assignee, category, due_date, urgent):
    """Sends NEW TASK notification"""
    if not SLACK_WEBHOOK_URL: return
    
    slack_tag = get_slack_tag(assignee)
    icon = "🔥" if urgent else "📋"
    priority_text = "*URGENT PRIORITY*" if urgent else "New Task"
    
    payload = {
        "text": f"{icon} {priority_text} for {slack_tag}: {task}",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"{icon} *{priority_text}*\n*{task}*"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Category:*\n{category}"},
                {"type": "mrkdwn", "text": f"*Assignee:*\n{slack_tag}"},
                {"type": "mrkdwn", "text": f"*Due Date:*\n{due_date.strftime('%b %d • %I:%M %p')}"}
            ]}
        ]
    }
    try: requests.post(SLACK_WEBHOOK_URL, json=payload)
    except: pass

def send_slack_completion_notification(task, assignee, category):
    """Sends COMPLETED TASK notification"""
    if not SLACK_WEBHOOK_URL: return

    slack_tag = get_slack_tag(assignee)
    
    payload = {
        "text": f"✅ Task Completed: {task}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ *Task Completed*\n*{task}*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Completed By:*\n{slack_tag}"},
                    {"type": "mrkdwn", "text": f"*Category:*\n{category}"}
                ]
            }
        ]
    }
    try: requests.post(SLACK_WEBHOOK_URL, json=payload)
    except: pass

def check_funding_deadline():
    now = datetime.now()
    deadline = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if now > deadline: deadline += timedelta(days=1)
    time_left = deadline - now
    return int(time_left.total_seconds() // 3600), int((time_left.total_seconds() % 3600) // 60), time_left.total_seconds() < 3600

def generate_gcal_link(title, due_datetime):
    base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    start = due_datetime.strftime("%Y%m%dT%H%M%S")
    end = (due_datetime + timedelta(hours=1)).strftime("%Y%m%dT%H%M%S")
    return f"{base}&text={title.replace(' ', '+')}&dates={start}/{end}"

def toggle_status(index):
    st.session_state.tasks.at[index, 'Status'] = not st.session_state.tasks.at[index, 'Status']

# --- 4. UI STRUCTURE ---
today_str = datetime.now().strftime("%A, %B %d, %Y")
st.markdown(f"""
<div class="finance-banner">
    <div style="display: flex; align-items: center; gap: 20px;">
        <span style="font-size: 50px; background: rgba(255,255,255,0.2); padding: 10px; border-radius: 50%;">👨‍💼👩‍💼</span>
        <div><h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">Finance Operations Team</h1>
        <p style="color: #e0e7ff; margin: 0; font-size: 16px; opacity: 0.9;">Daily Task Manager & Tracking</p></div>
    </div>
    <div style="text-align: right;"><div style="font-size: 22px; font-weight: bold; color: white;">{today_str}</div></div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.subheader("🔧 Diagnostics")
    if st.button("🔔 Test Slack Connection"):
        if not SLACK_WEBHOOK_URL: st.error("URL missing in Secrets")
        else:
            r = requests.post(SLACK_WEBHOOK_URL, json={"text": "🔔 Test: Connection working!"})
            if r.status_code == 200: st.success("Success!")
            else: st.error(f"Error: {r.status_code}")
                
    st.divider()
    st.subheader("➕ New Activity")
    with st.form("add_task_form", clear_on_submit=True):
        new_task = st.text_input("Task Name")
        new_cat = st.selectbox("Category", CATEGORIES)
        new_assignee = st.selectbox("Assignee", TEAM[1:])
        c_date, c_time = st.columns(2)
        input_date = c_date.date_input("Due Date", value=datetime.now())
        input_time = c_time.time_input("Due Time", value=time(12, 00))
        is_urgent = st.checkbox("Urgent Priority")
        
        if st.form_submit_button("Add Task"):
            final_due_dt = datetime.combine(input_date, input_time)
            new_entry = {"Task": new_task, "Category": new_cat, "Assignee": new_assignee, "Due Date": final_due_dt, "Status": False, "Urgent": is_urgent}
            st.session_state.tasks = pd.concat([pd.DataFrame([new_entry]), st.session_state.tasks], ignore_index=True)
            send_slack_notification(new_task, new_assignee, new_cat, final_due_dt, is_urgent)
            st.rerun()

hours, mins, is_urgent_time = check_funding_deadline()
col_h1, col_h2, col_h3 = st.columns(3)
with col_h1: st.metric("Pending Tasks", len(st.session_state.tasks[st.session_state.tasks["Status"] == False]))
with col_h2: st.metric("Completed Today", len(st.session_state.archived[st.session_state.archived["Completed At"].str.startswith(datetime.now().strftime("%Y-%m-%d"))]))
with col_h3:
    color = "#e11d48" if is_urgent_time else "#4f46e5"
    st.markdown(f"""<div style="background: white; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
        <span style="color: #64748b; font-size: 11px; font-weight: bold; letter-spacing: 1px;">DAILY FUNDING CUTOFF</span><br>
        <span style="color: {color}; font-size: 26px; font-weight: 800; font-family: monospace;">{hours}h {mins}m</span></div>""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- TASK GRID ---
active_tasks = st.session_state.tasks
grid_cols = st.columns(3)
for i, category in enumerate(CATEGORIES):
    col_idx = i % 3
    with grid_cols[col_idx]:
        cat_tasks = active_tasks[active_tasks["Category"] == category]
        card_type = "urgent-card" if "Daily Funding" in category else "normal-card"
        st.markdown(f"""<div class="category-card {card_type}"><h3 style="font-size: 16px; margin-bottom: 15px; font-weight: 600;">{category}</h3>""", unsafe_allow_html=True)
        if cat_tasks.empty:
            st.markdown("<div style='color: #cbd5e1; text-align: center; padding: 10px;'>No active tasks</div>", unsafe_allow_html=True)
        else:
            for idx, row in cat_tasks.iterrows():
                c1, c2 = st.columns([0.15, 0.85])
                done = c1.checkbox("", value=row["Status"], key=f"check_{idx}", on_change=toggle_status, args=(idx,))
                due_dt_str = row['Due Date'].strftime('%b %d • %I:%M %p')
                gcal_link = generate_gcal_link(row['Task'], row['Due Date'])
                task_style = "text-decoration: line-through; color: #94a3b8;" if row["Status"] else "font-weight: 500; color: #334155;"
                urgent_badge = "<span style='background:#fee2e2; color:#ef4444; font-size:10px; padding:2px 6px; border-radius:4px;'>URGENT</span>" if row["Urgent"] else ""
                c2.markdown(f"""<div style="line-height: 1.4; margin-bottom: 8px;"><span style="{task_style} font-size: 14px;">{row['Task']}</span><br>
                    <div style="margin-top:4px;"><span style="font-size: 11px; color: #64748b; background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">👤 {row['Assignee']}</span>
                    <span style="font-size: 11px; color: #64748b; margin-left: 5px;">📅 {due_dt_str} {urgent_badge}</span></div>
                    <div style="margin-top:5px; text-align: right;"><a href="{gcal_link}" target="_blank" style="text-decoration:none; color: #4f46e5; font-size: 10px; font-weight: bold;">+ Add to G-Cal</a></div></div>
                <div style="border-bottom: 1px solid #f1f5f9; margin: 8px 0;"></div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- ARCHIVE BUTTON (BOTTOM OF PAGE) ---
st.markdown("<br><hr>", unsafe_allow_html=True)
completed_tasks = st.session_state.tasks[st.session_state.tasks["Status"] == True]
completed_tasks_count = len(completed_tasks)

if completed_tasks_count > 0:
    col_a, col_b = st.columns([4, 1])
    with col_b:
        # PRIMARY ACTION BUTTON
        if st.button(f"📥 Archive ({completed_tasks_count}) Completed Tasks", type="primary", use_container_width=True):
            
            # 1. SEND SLACK NOTIFICATIONS FOR EACH COMPLETED TASK
            for index, row in completed_tasks.iterrows():
                send_slack_completion_notification(row['Task'], row['Assignee'], row['Category'])
            
            # 2. MOVE TO ARCHIVE
            to_archive = completed_tasks.copy()
            to_archive["Completed At"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.archived = pd.concat([st.session_state.archived, to_archive], ignore_index=True)
            
            # 3. REMOVE FROM ACTIVE
            st.session_state.tasks = st.session_state.tasks[st.session_state.tasks["Status"] == False]
            
            st.success("Tasks archived & Slack notifications sent!")
            st.rerun()

with st.expander("📂 View Archived History"):
    st.dataframe(st.session_state.archived, use_container_width=True)


