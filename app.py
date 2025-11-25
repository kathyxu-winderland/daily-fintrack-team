import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="FinTrack Sync", page_icon="📈", layout="wide")

# Custom CSS for the "Card" Look
st.markdown("""
<style>
    .main { background-color: #f1f5f9; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #0f172a; }
    
    /* Card Styling */
    div[data-testid="column"] {
        background-color: transparent;
    }
    
    .category-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    .urgent-card {
        border-top: 5px solid #e11d48;
    }
    
    .normal-card {
        border-top: 5px solid #6366f1;
    }

    /* Metric Styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA SETUP ---

CATEGORIES = [
    "💸 Daily Funding (12PM)",
    "📊 Budget 2026",
    "🤝 Revenue Share",
    "🏦 ATB Reporting",
    "🔄 SOFR Renewal",
    "🔐 GIC"
]

TEAM = ["All", "Jason", "Amanda", "Raj", "Finance Lead"]

# Initialize Session State
if 'tasks' not in st.session_state:
    st.session_state.tasks = pd.DataFrame([
        {"Task": "Approve Wire Transfers", "Category": "💸 Daily Funding (12PM)", "Assignee": TEAM[1], "Due Time": time(11, 30), "Status": False, "Urgent": True},
        {"Task": "Verify Cash Position", "Category": "💸 Daily Funding (12PM)", "Assignee": TEAM[1], "Due Time": time(10, 00), "Status": False, "Urgent": True},
        {"Task": "Q2 Variance Analysis", "Category": "📊 Budget 2026", "Assignee": TEAM[2], "Due Time": time(16, 00), "Status": False, "Urgent": False},
        {"Task": "Submit Compliance Doc", "Category": "🏦 ATB Reporting", "Assignee": TEAM[3], "Due Time": time(9, 00), "Status": False, "Urgent": False},
    ])

if 'archived' not in st.session_state:
    st.session_state.archived = pd.DataFrame(columns=["Task", "Category", "Assignee", "Due Time", "Status", "Urgent", "Completed At"])

# --- 3. HELPER FUNCTIONS ---

def check_funding_deadline():
    now = datetime.now()
    deadline = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if now > deadline:
        deadline = deadline + timedelta(days=1)
    time_left = deadline - now
    hours = int(time_left.total_seconds() // 3600)
    mins = int((time_left.total_seconds() % 3600) // 60)
    return hours, mins, time_left.total_seconds() < 3600

def toggle_status(index):
    st.session_state.tasks.at[index, 'Status'] = not st.session_state.tasks.at[index, 'Status']

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🏦 FinTrack")
    
    # Add Task Form moved to Sidebar for cleaner UI
    st.subheader("➕ New Activity")
    with st.form("add_task_form", clear_on_submit=True):
        new_task = st.text_input("Task Name")
        new_cat = st.selectbox("Category", CATEGORIES)
        new_assignee = st.selectbox("Assignee", TEAM[1:])
        new_time = st.time_input("Due", value=time(12, 00))
        is_urgent = st.checkbox("Urgent Priority")
        if st.form_submit_button("Add Task"):
            new_entry = {
                "Task": new_task, "Category": new_cat, 
                "Assignee": new_assignee, "Due Time": new_time, 
                "Status": False, "Urgent": is_urgent
            }
            st.session_state.tasks = pd.concat([pd.DataFrame([new_entry]), st.session_state.tasks], ignore_index=True)
            st.rerun()
            
    st.divider()
    
    # Archive Logic
    completed_count = len(st.session_state.tasks[st.session_state.tasks["Status"] == True])
    if completed_count > 0:
        st.success(f"{completed_count} tasks completed!")
        if st.button(f"📥 Archive Completed"):
            completed = st.session_state.tasks[st.session_state.tasks["Status"] == True].copy()
            completed["Completed At"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.archived = pd.concat([st.session_state.archived, completed], ignore_index=True)
            st.session_state.tasks = st.session_state.tasks[st.session_state.tasks["Status"] == False]
            st.rerun()

# --- 5. MAIN DASHBOARD ---

# Header Stats
hours, mins, is_urgent_time = check_funding_deadline()
col_h1, col_h2, col_h3 = st.columns(3)

with col_h1:
    st.metric("Pending Tasks", len(st.session_state.tasks[st.session_state.tasks["Status"] == False]))
with col_h2:
    st.metric("Completed Today", len(st.session_state.archived[st.session_state.archived["Completed At"].str.startswith(datetime.now().strftime("%Y-%m-%d"))]))
with col_h3:
    # Custom Funding Timer
    color = "red" if is_urgent_time else "blue"
    st.markdown(f"""
    <div style="background: white; padding: 10px; border-radius: 8px; border: 1px solid #ddd; text-align: center;">
        <span style="color: gray; font-size: 12px;">DAILY FUNDING CUTOFF</span><br>
        <span style="color: {color}; font-size: 24px; font-weight: bold;">{hours}h {mins}m</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- 6. THE GRID VIEW (THE NEW BLOCKS) ---

# We filter tasks that are NOT completed yet (Active)
active_tasks = st.session_state.tasks

# Create 3 Columns for our Grid
grid_cols = st.columns(3)

# Loop through categories and place them in columns
for i, category in enumerate(CATEGORIES):
    # Determine which column this category goes into (0, 1, or 2)
    col_idx = i % 3
    
    with grid_cols[col_idx]:
        # Filter tasks for this specific category
        cat_tasks = active_tasks[active_tasks["Category"] == category]
        
        # Determine Card Style (Red for Funding, Blue for others)
        card_type = "urgent-card" if "Daily Funding" in category else "normal-card"
        
        # Start HTML Card
        st.markdown(f"""<div class="category-card {card_type}"><h3>{category}</h3>""", unsafe_allow_html=True)
        
        if cat_tasks.empty:
            st.markdown("<p style='color: #94a3b8; font-style: italic; font-size: 14px;'>No active tasks</p>", unsafe_allow_html=True)
        else:
            # Iterate through tasks in this category
            for idx, row in cat_tasks.iterrows():
                # We create a container for each task line
                c1, c2 = st.columns([0.15, 0.85])
                
                # Checkbox (Logic)
                # We use the unique index as the key to avoid conflicts
                done = c1.checkbox("", value=row["Status"], key=f"check_{idx}", on_change=toggle_status, args=(idx,))
                
                # Text (Visual)
                task_style = "text-decoration: line-through; color: gray;" if row["Status"] else "font-weight: 500;"
                urgent_badge = "🔥" if row["Urgent"] else ""
                
                c2.markdown(f"""
                <div style="line-height: 1.2; margin-top: 5px;">
                    <span style="{task_style}">{row['Task']}</span> <br>
                    <span style="font-size: 11px; color: #64748b;">👤 {row['Assignee']} • ⏰ {row['Due Time'].strftime('%I:%M %p')} {urgent_badge}</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        # End HTML Card
        st.markdown("</div>", unsafe_allow_html=True)

# History Tab at the bottom
with st.expander("📂 View Archived History"):
    st.dataframe(st.session_state.archived, use_container_width=True)
