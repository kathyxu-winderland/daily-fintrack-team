import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Budget 2026 Tracker", page_icon="💰", layout="wide")

# !!! PASTE YOUR SLACK WEBHOOK URL HERE !!!
SLACK_WEBHOOK_URL = ""

# Department Configuration
DEPT_COLORS = {
    "🎧 Customer Care": "#f97316",       # Orange
    "💻 Development": "#3b82f6",         # Blue
    "💰 Finance": "#10b981",             # Emerald
    "📢 Marketing": "#ec4899",           # Pink
    "🖥️ IT Operation": "#64748b",        # Slate
    "📈 Data & Rev Op": "#8b5cf6",       # Violet
    "🚀 Product, Sales & Success": "#6366f1", # Indigo
    "⚖️ Legal": "#d97706",               # Amber
    "👔 Leadership": "#111827",          # Black
    "💜 People & Culture": "#06b6d4"     # Cyan
}

TEAM = ["All", "Dept Head", "Alex", "Sarah", "Mike", "Exec Team"]

# Custom CSS - The "Top Tier" Design System
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .main { background-color: #f8fafc; }
    
    h1, h2, h3, h4, p, div, span { font-family: 'Inter', sans-serif; }
    
    /* MAIN BANNER */
    .budget-banner {
        background: linear-gradient(120deg, #0f172a 0%, #334155 100%);
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 40px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* KANBAN CARD CONTAINER */
    .kanban-card {
        background-color: white;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
        margin-bottom: 24px;
        overflow: hidden; /* Keeps header inside border radius */
        transition: all 0.2s ease;
    }
    .kanban-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 16px -4px rgba(0, 0, 0, 0.08);
    }
    
    /* CARD HEADER */
    .card-header {
        padding: 16px 20px;
        border-bottom: 1px solid #f1f5f9;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* TASK ROW styling */
    .task-row {
        padding: 12px 20px;
        border-bottom: 1px solid #f8fafc;
    }
    .task-row:last-child { border-bottom: none; }
    
    /* PILLS & BADGES */
    .meta-pill {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 6px;
    }
    .assignee-pill { background-color: #f1f5f9; color: #475569; }
    .cost-pill { background-color: #ecfdf5; color: #059669; letter-spacing: 0.5px; }
    
    /* CHECKBOX OVERRIDE */
    div[data-testid="stCheckbox"] label {
        padding-top: 2px;
    }
    
    /* BUTTONS */
    .stButton button {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        transition: all 0.2s;
    }
    .stButton button:hover {
        border-color: #cbd5e1;
        background-color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA SETUP ---

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

# --- 3. LOGIC & SLACK ---

def send_slack_alert(task, dept, cost, assignee, is_reminder=False):
    if not SLACK_WEBHOOK_URL: return
    formatted_cost = f"${cost:,.2f}"
    
    if is_reminder:
        title, emoji, color, pretext = "Item Reminder", "🔔", "#f59e0b", f"Hey *{assignee}*, update needed:"
    else:
        title, emoji, color, pretext = "New Request", "💸", "#10b981", "New budget item added:"

    payload = {
        "text": f"{emoji} {title}: {task}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {title}"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Dept:* {dept}"},
                {"type": "mrkdwn", "text": f"*Cost:* {formatted_cost}"},
                {"type": "mrkdwn", "text": f"*Task:* {task}"},
                {"type": "mrkdwn", "text": f"*Who:* {assignee}"}
            ]}
        ]
    }
    try: requests.post(SLACK_WEBHOOK_URL, json=payload)
    except: pass

def toggle_status(index):
    st.session_state.budget_tasks.at[index, 'Status'] = not st.session_state.budget_tasks.at[index, 'Status']

# --- 4. TOP BANNER ---
total_spend = st.session_state.budget_tasks["Cost"].sum()
formatted_spend = f"${total_spend:,.2f}"
pending_count = len(st.session_state.budget_tasks[st.session_state.budget_tasks["Status"] == False])

st.markdown(f"""
<div class="budget-banner">
    <div style="display: flex; align-items: center; gap: 24px;">
        <div style="background: rgba(255,255,255,0.15); padding: 16px; border-radius: 16px; backdrop-filter: blur(5px);">
            <span style="font-size: 40px;">🏦</span>
        </div>
        <div>
            <h1 style="color: white; margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px;">Budget Master 2026</h1>
            <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 15px;">Tracking {len(st.session_state.budget_tasks)} line items across departments</p>
        </div>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; font-weight: 600;">Projected Spend</div>
        <div style="font-size: 36px; font-weight: 800; color: white; letter-spacing: -1px;">{formatted_spend}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.subheader("➕ New Request")
    with st.form("add_budget_form", clear_on_submit=True):
        new_task = st.text_input("Line Item Name")
        new_dept = st.selectbox("Department", list(DEPT_COLORS.keys()))
        new_assignee = st.selectbox("Assignee", TEAM[1:])
        new_cost = st.number_input("Est. Cost ($)", min_value=0.0, step=100.0)
        new_date = st.date_input("Deadline", value=datetime.now() + timedelta(days=7))
        
        if st.form_submit_button("Add to Board"):
            new_entry = {
                "Task": new_task, "Department": new_dept, 
                "Assignee": new_assignee, "Due Date": pd.to_datetime(new_date), 
                "Cost": new_cost, "Status": False
            }
            st.session_state.budget_tasks = pd.concat([pd.DataFrame([new_entry]), st.session_state.budget_tasks], ignore_index=True)
            if SLACK_WEBHOOK_URL:
                send_slack_alert(new_task, new_dept, new_cost, new_assignee)
                st.toast("Notification sent to Slack!", icon="🚀")
            st.rerun()
            
    st.markdown("---")
    csv = st.session_state.budget_tasks.to_csv(index=False).encode('utf-8')
    st.download_button(label="📄 Export to Excel/CSV", data=csv, file_name='budget_2026.csv', mime='text/csv')

# --- 6. MODERN GRID LAYOUT ---
grid_cols = st.columns(3)

for i, (dept_name, dept_color) in enumerate(DEPT_COLORS.items()):
    col_idx = i % 3
    with grid_cols[col_idx]:
        dept_tasks = st.session_state.budget_tasks[st.session_state.budget_tasks["Department"] == dept_name]
        dept_total = dept_tasks["Cost"].sum()
        
        # 1. THE CARD CONTAINER START
        # We use a soft background color (hex + '15' opacity) for the header
        header_bg = f"{dept_color}15" 
        
        st.markdown(f"""
        <div class="kanban-card">
            <div class="card-header" style="background-color: {header_bg};">
                <span style="font-weight: 700; color: {dept_color}; font-size: 14px;">{dept_name}</span>
                <span style="font-size: 12px; font-weight: 700; color: {dept_color}; opacity: 0.9;">${dept_total:,.0f}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # 2. TASK ITEMS LOOP
        if dept_tasks.empty:
            st.markdown("<div style='padding: 30px; text-align: center; color: #cbd5e1; font-size: 13px;'>No requests</div>", unsafe_allow_html=True)
        else:
            for idx, row in dept_tasks.iterrows():
                # Grid for Row Content
                c1, c2, c3 = st.columns([0.15, 0.70, 0.15])
                
                # Checkbox
                c1.checkbox("", value=row["Status"], key=f"b_{idx}", on_change=toggle_status, args=(idx,))
                
                # Content
                # Logic for strike-through text
                t_style = "text-decoration: line-through; color: #cbd5e1;" if row["Status"] else "font-weight: 600; color: #334155;"
                cost_str = f"${row['Cost']:,.0f}" if row['Cost'] > 0 else "TBD"
                
                c2.markdown(f"""
                <div style="padding-top: 2px;">
                    <div style="{t_style} font-size: 14px; margin-bottom: 6px;">{row['Task']}</div>
                    <div style="display: flex; align-items: center;">
                        <span class="meta-pill assignee-pill">👤 {row['Assignee']}</span>
                        <span class="meta-pill cost-pill">{cost_str}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Button (Only show if active)
                if not row["Status"]:
                    if c3.button("🔔", key=f"n_{idx}", help="Nudge on Slack"):
                         if SLACK_WEBHOOK_URL:
                            send_slack_alert(row['Task'], row['Department'], row['Cost'], row['Assignee'], is_reminder=True)
                            st.toast("Nudged!", icon="🔔")

                # Visual Separator (Markdown) to mimic row line
                st.markdown("<div style='border-bottom: 1px solid #f8fafc; margin: 8px 0;'></div>", unsafe_allow_html=True)

        # 3. CARD CONTAINER END
        st.markdown("</div>", unsafe_allow_html=True)
