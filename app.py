import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="FinTrack Sync", page_icon="📈", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; color: #1e293b; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
    .urgent-box { border-left: 5px solid #e11d48; background-color: #fff1f2; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .normal-box { border-left: 5px solid #4f46e5; background-color: #eef2ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .stButton button { width: 100%; border-radius: 5px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA SETUP ---

# Categories Configuration with ICONS
CATEGORIES = [
    "💸 Daily Funding (12PM Cutoff)",
    "📊 Budget 2026",
    "🤝 Revenue Share",
    "🏦 ATB Reporting",
    "🔄 SOFR Renewal",
    "🔐 GIC"
]

# Team Members - EDIT THESE NAMES
TEAM = ["All", "Jason", "Amanda", "Raj", "Finance Lead"] 

# Initialize Session State (Mock Database)
if 'tasks' not in st.session_state:
    st.session_state.tasks = pd.DataFrame([
        {"Task": "Approve Wire Transfers", "Category": "💸 Daily Funding (12PM Cutoff)", "Assignee": TEAM[1], "Due Time": time(11, 30), "Status": False, "Urgent": True},
        {"Task": "Q2 Variance Analysis", "Category": "📊 Budget 2026", "Assignee": TEAM[2], "Due Time": time(16, 00), "Status": False, "Urgent": False},
        {"Task": "Submit Compliance Doc", "Category": "🏦 ATB Reporting", "Assignee": TEAM[3], "Due Time": time(9, 00), "Status": False, "Urgent": False},
    ])

# Initialize Archive State
if 'archived' not in st.session_state:
    st.session_state.archived = pd.DataFrame(columns=["Task", "Category", "Assignee", "Due Time", "Status", "Urgent", "Completed At"])

# --- 3. HELPER FUNCTIONS ---

def generate_gcal_link(title, due_time):
    base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    today = datetime.now().strftime("%Y%m%d")
    start = f"{today}T{due_time.strftime('%H%M%S')}"
    end = f"{today}T{(datetime.combine(datetime.today(), due_time) + timedelta(hours=1)).strftime('%H%M%S')}"
    return f"{base}&text={title.replace(' ', '+')}&dates={start}/{end}"

def check_funding_deadline():
    now = datetime.now()
    deadline = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if now > deadline:
        deadline = deadline + timedelta(days=1)
    time_left = deadline - now
    hours = int(time_left.total_seconds() // 3600)
    mins = int((time_left.total_seconds() % 3600) // 60)
    return hours, mins, time_left.total_seconds() < 3600

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🏦 FinTrack Manager")
    st.markdown("### Filters")
    selected_user = st.selectbox("View Tasks For:", TEAM)
    selected_cat = st.multiselect("Filter Category", CATEGORIES, default=CATEGORIES)
    st.divider()
    st.info("💡 **Tip:** Check the box to complete a task, then click 'Archive' to clear the board.")

# --- 5. MAIN DASHBOARD ---

hours, mins, is_urgent = check_funding_deadline()

# Top Section
col1, col2 = st.columns([2, 1])
with col1:
    st.title(f"Dashboard")
    st.caption(f"Date: {datetime.now().strftime('%A, %b %d')}")
with col2:
    bg_class = "urgent-box" if is_urgent else "normal-box"
    st.markdown(f"""
    <div class="{bg_class}">
        <h3 style="margin:0">💸 Daily Funding</h3>
        <p style="font-size: 24px; font-weight: bold; margin: 5px 0 0 0;">{hours}h {mins}m remaining</p>
        <small>12:00 PM Hard Cut-off</small>
    </div>
    """, unsafe_allow_html=True)

# Tabs for Active vs History
tab1, tab2 = st.tabs(["⚡ Active Tasks", "📂 Archived History"])

with tab1:
    # ADD NEW TASK EXPANDER
    with st.expander("➕ Add New Activity", expanded=False):
        with st.form("add_task_form"):
            c1, c2, c3 = st.columns(3)
            new_task = c1.text_input("Task Name")
            new_cat = c2.selectbox("Category", CATEGORIES)
            new_assignee = c3.selectbox("Assign to", TEAM[1:]) 
            
            c4, c5 = st.columns(2)
            new_time = c4.time_input("Due Time", value=time(12, 00))
            is_urgent_flag = c5.checkbox("Mark as Urgent")
            submitted = st.form_submit_button("Create Task")
            
            if submitted and new_task:
                new_entry = {
                    "Task": new_task, "Category": new_cat, 
                    "Assignee": new_assignee, "Due Time": new_time, 
                    "Status": False, "Urgent": is_urgent_flag
                }
                st.session_state.tasks = pd.concat([pd.DataFrame([new_entry]), st.session_state.tasks], ignore_index=True)
                st.rerun()

    # FILTER LOGIC
    df = st.session_state.tasks
    if selected_user != "All":
        df = df[df["Assignee"] == selected_user]
    if selected_cat:
        df = df[df["Category"].isin(selected_cat)]

    # DATA EDITOR (The Task List)
    st.subheader("Your Activities")
    
    # We use column_config to make the Category dropdown width distinct
    edited_df = st.data_editor(
        df,
        column_config={
            "Status": st.column_config.CheckboxColumn("Done", width="small", default=False),
            "Category": st.column_config.SelectboxColumn("Category", options=CATEGORIES, width="medium"),
            "Assignee": st.column_config.SelectboxColumn("Assignee", options=TEAM, width="small"),
            "Due Time": st.column_config.TimeColumn("Due By", format="h:mm a"),
            "Urgent": st.column_config.CheckboxColumn("Urgent", width="small", default=False),
        },
        disabled=["Task"],
        hide_index=True,
        use_container_width=True,
        key="editor"
    )

    # Update session state
    if not df.equals(edited_df):
        st.session_state.tasks.update(edited_df)
        st.rerun()

    # ACTION BUTTONS
    col_act1, col_act2 = st.columns([1, 3])
    
    with col_act1:
        # ARCHIVE LOGIC
        completed_tasks = st.session_state.tasks[st.session_state.tasks["Status"] == True]
        if not completed_tasks.empty:
            if st.button(f"📥 Archive ({len(completed_tasks)}) Completed"):
                completed_tasks["Completed At"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.archived = pd.concat([st.session_state.archived, completed_tasks], ignore_index=True)
                st.session_state.tasks = st.session_state.tasks[st.session_state.tasks["Status"] == False]
                st.success("Tasks moved to Archive!")
                st.rerun()

    with col_act2:
        # GOOGLE CALENDAR LOGIC
        pending_urgent = st.session_state.tasks[(st.session_state.tasks['Status'] == False)]
        if not pending_urgent.empty:
            top_task = pending_urgent.iloc[0]
            cal_link = generate_gcal_link(top_task['Task'], top_task['Due Time'])
            st.markdown(f"""
            <div style="text-align: right;">
                <a href="{cal_link}" target="_blank" style="text-decoration: none;">
                    <span style="color: #4f46e5; font-weight: bold; cursor: pointer;">📅 Add top task to Google Calendar &rarr;</span>
                </a>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.subheader("📜 Activity History")
    if st.session_state.archived.empty:
        st.info("No archived tasks yet.")
    else:
        st.dataframe(
            st.session_state.archived,
            column_config={
                "Status": None, 
                "Completed At": st.column_config.TextColumn("Completed At")
            },
            hide_index=True,
            use_container_width=True
        )
