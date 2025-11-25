import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import plotly.express as px

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="FinTrack Sync", page_icon="📈", layout="wide")

# Custom CSS to make it look "Top Tier"
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; color: #1e293b; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
    .css-1d391kg { padding-top: 2rem; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; border: 1px solid #e2e8f0; }
    .big-font { font-size: 18px !important; font-weight: 500; color: #334155; }
    .urgent-box { border-left: 5px solid #e11d48; background-color: #fff1f2; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .normal-box { border-left: 5px solid #4f46e5; background-color: #eef2ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA SETUP ---

# Categories Configuration
CATEGORIES = [
    "1. Daily Funding (12PM Cutoff)",
    "2. Budget 2026",
    "3. Revenue Share",
    "4. ATB Reporting",
    "5. SOFR Renewal",
    "6. GIC"
]

TEAM = ["All", "Alex", "Sarah", "Mike", "Team Lead"]

# Initialize Session State (Mock Database)
if 'tasks' not in st.session_state:
    st.session_state.tasks = pd.DataFrame([
        {"Task": "Approve Wire Transfers", "Category": "1. Daily Funding (12PM Cutoff)", "Assignee": "Alex", "Due Time": time(11, 30), "Status": False, "Urgent": True},
        {"Task": "Q2 Variance Analysis", "Category": "2. Budget 2026", "Assignee": "Sarah", "Due Time": time(16, 00), "Status": True, "Urgent": False},
        {"Task": "Submit Compliance Doc", "Category": "4. ATB Reporting", "Assignee": "Mike", "Due Time": time(9, 00), "Status": False, "Urgent": False},
    ])

# --- 3. HELPER FUNCTIONS ---

def generate_gcal_link(title, due_time):
    # Create a smart link to open Google Calendar with details pre-filled
    base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    # Set date to today
    today = datetime.now().strftime("%Y%m%d")
    # Format: YYYYMMDDTHHMMSSZ
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
    
    return hours, mins, time_left.total_seconds() < 3600 # True if < 1 hour (Urgent)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🏦 FinTrack Manager")
    st.image("https://ui-avatars.com/api/?name=Fin+Ops&background=4f46e5&color=fff", width=50)
    
    st.markdown("### Filters")
    selected_user = st.selectbox("View Tasks For:", TEAM)
    selected_cat = st.multiselect("Filter Category", CATEGORIES, default=CATEGORIES)
    
    st.divider()
    st.info("💡 **Tip:** Click the checkbox in the table to mark items as complete.")

# --- 5. MAIN DASHBOARD ---

# HEADER & FUNDING CLOCK
hours, mins, is_urgent = check_funding_deadline()

col1, col2 = st.columns([2, 1])

with col1:
    st.title(f"Dashboard: {datetime.now().strftime('%A, %b %d')}")
    st.markdown("Track daily financial operations and compliance tasks.")

with col2:
    # Visual Funding Countdown
    color = "red" if is_urgent else "blue"
    bg_class = "urgent-box" if is_urgent else "normal-box"
    
    st.markdown(f"""
    <div class="{bg_class}">
        <h3 style="margin:0">💰 Daily Funding Cutoff</h3>
        <p style="font-size: 24px; font-weight: bold; margin: 5px 0 0 0;">
            {hours}h {mins}m remaining
        </p>
        <small>Deadline: 12:00 PM</small>
    </div>
    """, unsafe_allow_html=True)

# ADD NEW TASK
with st.expander("➕ Add New Activity", expanded=False):
    with st.form("add_task_form"):
        c1, c2, c3 = st.columns(3)
        new_task = c1.text_input("Task Name")
        new_cat = c2.selectbox("Category", CATEGORIES)
        new_assignee = c3.selectbox("Assign to", TEAM[1:]) # Skip "All"
        
        c4, c5, c6 = st.columns(3)
        new_time = c4.time_input("Due Time", value=time(12, 00))
        is_urgent_flag = c5.checkbox("Mark as Urgent / High Priority")
        submitted = st.form_submit_button("Create Task")
        
        if submitted and new_task:
            new_entry = {
                "Task": new_task, "Category": new_cat, 
                "Assignee": new_assignee, "Due Time": new_time, 
                "Status": False, "Urgent": is_urgent_flag
            }
            # Append to session state
            st.session_state.tasks = pd.concat([
                pd.DataFrame([new_entry]), 
                st.session_state.tasks
            ], ignore_index=True)
            st.rerun()

# DISPLAY TASKS
st.divider()

# Filter Logic
df = st.session_state.tasks
if selected_user != "All":
    df = df[df["Assignee"] == selected_user]
if selected_cat:
    df = df[df["Category"].isin(selected_cat)]

# Interactive Data Editor
edited_df = st.data_editor(
    df,
    column_config={
        "Status": st.column_config.CheckboxColumn(
            "Done",
            help="Check to mark as completed",
            default=False,
        ),
        "Category": st.column_config.SelectboxColumn(
            "Category",
            options=CATEGORIES,
            width="medium"
        ),
        "Assignee": st.column_config.SelectboxColumn(
            "Assignee",
            options=TEAM,
            width="small"
        ),
        "Due Time": st.column_config.TimeColumn(
            "Due By",
            format="h:mm a"
        )
    },
    disabled=["Task"], # Prevent changing task names directly (optional)
    hide_index=True,
    use_container_width=True,
    num_rows="fixed"
)

# SYNC BACK TO STATE (To save checkbox clicks)
st.session_state.tasks = edited_df

# GOOGLE CALENDAR ACTIONS
st.subheader("📅 Calendar Actions")
if not df.empty:
    # Find the first unchecked task to suggest adding to calendar
    pending_tasks = df[df['Status'] == False]
    
    if not pending_tasks.empty:
        task_to_add = pending_tasks.iloc[0]
        cal_link = generate_gcal_link(task_to_add['Task'], task_to_add['Due Time'])
        
        st.markdown(f"""
        <a href="{cal_link}" target="_blank" style="text-decoration: none;">
            <button style="background-color: #4285F4; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">
                📅 Add "{task_to_add['Task']}" to Google Calendar
            </button>
        </a>
        """, unsafe_allow_html=True)
    else:
        st.success("All tasks completed! 🎉")