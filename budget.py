import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Budget 2026 Tracker", page_icon="💰", layout="wide")

# !!! PASTE YOUR SLACK WEBHOOK URL HERE !!!
SLACK_WEBHOOK_URL = ""

# Department Configuration with Specific Colors
# Format: "Name": "Hex Color Code"
DEPT_COLORS = {
    "🎧 Customer Care": "#f97316",       # Orange
    "💻 Development": "#3b82f6",         # Blue
    "💰 Finance": "#10b981",             # Emerald
    "📢 Marketing": "#ec4899",           # Pink
    "🖥️ IT Operation": "#64748b",        # Slate
    "📈 Data & Rev Op": "#8b5cf6",       # Violet
    "🚀 Product, Sales & Success": "#6366f1", # Indigo
    "⚖️ Legal": "#d97706",               # Amber
    "👔 Leadership": "#111827",          # Black/Dark
    "💜 People & Culture": "#06b6d4"     # Cyan
}

TEAM = ["All", "Dept Head", "Alex", "Sarah", "Mike", "Exec Team"]

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    h1, h2, h3, p { font-family: 'Inter', sans-serif; }
    
    /* BANNER STYLE */
    .budget-banner {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Card Styling */
    div[data-testid="column"] { background-color: transparent; }
    
    .dept-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .dept-card:hover { transform: translateY(-2px); }

</style>
""", unsafe_allow_html=True)

# --- 2. DATA SETUP ---

# Initialize Session State
if 'budget_tasks' not in st.session_state:
    st.session_state.budget_tasks = pd.DataFrame([
        {
            "Task": "Q1 Hiring Plan Review", 
            "Department": "💜 People & Culture", 
            "Assignee": "Sarah", 
            "Due Date": datetime.now() + timedelta(days=5), 
            "Cost": 2500.0,
            "Status": False
        },
        {
            "Task": "Server Infrastructure Upgrade", 
            "Department": "💻 Development", 
            "Assignee": "Mike", 
            "Due Date": datetime.now() + timedelta(days=14), 
            "Cost": 15000.0,
            "Status": False
        },
        {
            "Task": "2026 Ad Spend Strategy", 
            "Department": "📢 Marketing", 
            "Assignee": "Alex", 
            "Due Date": datetime.now() + timedelta(days=2), 
            "Cost": 50000.0,
            "Status": False
        },
    ])

# --- 3. HELPER FUNCTIONS ---

def send_slack_alert(task, dept, cost, assignee):
    """Sends a budget alert to Slack"""
    if not SLACK_WEBHOOK_URL:
        return
    
    formatted_cost = f"${cost:,.2f}"
    
    payload = {
        "text": f"💰 New Budget Item: {task} ({formatted_cost})",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "💰 New Budget Request"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Department:*\n{dept}"},
                    {"type": "mrkdwn", "text": f"*Est. Cost:*\n{formatted_cost}"},
                    {"type": "mrkdwn", "text": f"*Item:*\n{task}"},
                    {"type": "mrkdwn", "text": f"*Owner:*\n{assignee}"}
                ]
            }
        ]
    }
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload)
    except:
        pass

def toggle_status(index):
    st.session_state.budget_tasks.at[index, 'Status'] = not st.session_state.budget_tasks.at[index, 'Status']

# --- 4. BANNER SECTION (LIVE MATH) ---

# Calculate Total Spend Live
total_spend = st.session_state.budget_tasks["Cost"].sum()
formatted_spend = f"${total_spend:,.2f}"

st.markdown(f"""
<div class="budget-banner">
    <div style="display: flex; align-items: center; gap: 20px;">
        <span style="font-size: 50px; background: rgba(255,255,255,0.2); padding: 10px; border-radius: 50%;">📊</span>
        <div>
            <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">Budget 2026 Master</h1>
            <p style="color: #ecfdf5; margin: 0; font-size: 16px; opacity: 0.9;">Departmental Tracking & Approval</p>
        </div>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 14px; color: #d1fae5;">Total Projected Spend</div>
        <div style="font-size: 32px; font-weight: bold; color: white;">{formatted_spend}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.subheader("➕ Add Budget Item")
    with st.form("add_budget_form", clear_on_submit=True):
        new_task = st.text_input("Activity / Line Item")
        # Extract just the keys (names) for the dropdown
        new_dept = st.selectbox("Department", list(DEPT_COLORS.keys()))
        new_assignee = st.selectbox("Owner", TEAM[1:])
        new_cost = st.number_input("Est. Cost ($)", min_value=0.0, step=100.0)
        new_date = st.date_input("Deadline", value=datetime.now() + timedelta(days=7))
        
        if st.form_submit_button("Add Item"):
            new_entry = {
                "Task": new_task, "Department": new_dept, 
                "Assignee": new_assignee, "Due Date": pd.to_datetime(new_date), 
                "Cost": new_cost,
                "Status": False
            }
            # Add to state
            st.session_state.budget_tasks = pd.concat([pd.DataFrame([new_entry]), st.session_state.budget_tasks], ignore_index=True)
            
            # Send Slack Alert
            if SLACK_WEBHOOK_URL:
                send_slack_alert(new_task, new_dept, new_cost, new_assignee)
                st.toast("Budget item added & Slack team notified!", icon="🚀")
            
            st.rerun()
            
    st.divider()
    
    # Download Data Button
    csv = st.session_state.budget_tasks.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Budget CSV",
        data=csv,
        file_name='budget_2026.csv',
        mime='text/csv',
    )

# --- 6. DASHBOARD METRICS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Line Items", len(st.session_state.budget_tasks))
with col2:
    pending_count = len(st.session_state.budget_tasks[st.session_state.budget_tasks["Status"] == False])
    st.metric("Pending Approval/Action", pending_count)
with col3:
    # Calculate % completed
    total = len(st.session_state.budget_tasks)
    done = len(st.session_state.budget_tasks[st.session_state.budget_tasks["Status"] == True])
    progress = (done / total) if total > 0 else 0
    st.metric("Completion Progress", f"{progress:.0%}")
    st.progress(progress)

st.divider()

# --- 7. DEPARTMENT GRID (COLOR CODED) ---
grid_cols = st.columns(3)

# Iterate through departments
for i, (dept_name, dept_color) in enumerate(DEPT_COLORS.items()):
    col_idx = i % 3
    with grid_cols[col_idx]:
        # Filter tasks
        dept_tasks = st.session_state.budget_tasks[st.session_state.budget_tasks["Department"] == dept_name]
        
        # Calculate Dept Total
        dept_total = dept_tasks["Cost"].sum()
        
        # HTML for Color-Coded Card
        # We inject the 'dept_color' variable directly into the border-top and text color
        st.markdown(f"""
        <div class="dept-card" style="border-top: 5px solid {dept_color};">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <h3 style="font-size: 16px; margin:0; font-weight: 700; color: {dept_color};">{dept_name}</h3>
                <span style="background:{dept_color}15; color:{dept_color}; font-size:11px; padding:3px 8px; border-radius:4px; font-weight:bold;">${dept_total:,.0f}</span>
            </div>
        """, unsafe_allow_html=True)
        
        if dept_tasks.empty:
            st.markdown("<div style='color: #9ca3af; text-align: center; font-size: 13px; font-style:italic; padding-bottom:10px;'>No items</div>", unsafe_allow_html=True)
        else:
            for idx, row in dept_tasks.iterrows():
                c1, c2 = st.columns([0.15, 0.85])
                
                # Checkbox
                done = c1.checkbox("", value=row["Status"], key=f"bud_{idx}", on_change=toggle_status, args=(idx,))
                
                # Styling
                task_style = "text-decoration: line-through; color: #9ca3af;" if row["Status"] else "font-weight: 500; color: #1f2937;"
                cost_display = f"${row['Cost']:,.0f}" if row['Cost'] > 0 else "-"
                
                c2.markdown(f"""
                <div style="line-height: 1.3; margin-bottom: 8px;">
                    <span style="{task_style} font-size: 14px;">{row['Task']}</span><br>
                    <div style="display:flex; justify-content:space-between; margin-top:4px;">
                        <span style="font-size: 11px; color: #4b5563;">👤 {row['Assignee']}</span>
                        <span style="font-size: 11px; color: {dept_color}; font-weight:bold;">{cost_display}</span>
                    </div>
                </div>
                <div style="border-bottom: 1px dashed #e5e7eb; margin: 8px 0;"></div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
