import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Budget 2026 Tracker", page_icon="💰", layout="wide")

# !!! PASTE YOUR SLACK WEBHOOK URL HERE !!!
SLACK_WEBHOOK_URL = "hooks.slack.com/services/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"

# Department Configuration
DEPT_COLORS = {
    "🎧 Customer Care": "#f97316",       # Orange
    "💻 Development": "#3b82f6",         # Blue
    "💰 Finance": "#10b981",             # Emerald
    "📢 Marketing": "#ec4899",           # Pink
    "🖥️ IT Operation": "#64748b",        # Slate
    "📈 Data & Rev Op": "#8b5cf6",       # Violet
    "🚀 Product": "#6366f1",             # Indigo
    "💼 Sales & Success": "#0ea5e9",     # Sky Blue
    "⚖️ Legal": "#d97706",               # Amber
    "👔 Leadership": "#111827",          # Black
    "💜 People & Culture": "#06b6d4"     # Cyan
}

TEAM = ["All", "Tate", "Yuval", "Shane", "Shy", "Garth", "Agata", "Kike", "Karim", "Simon", "Jess"]

# Custom CSS
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
        margin-bottom: 30px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        display: flex; align-items: center; justify-content: space-between;
    }
    
    /* KANBAN CARD */
    .kanban-card {
        background-color: white; border-radius: 16px; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02); margin-bottom: 24px;
        overflow: hidden; transition: all 0.2s ease;
    }
    .kanban-card:hover { transform: translateY(-4px); box-shadow: 0 12px 16px -4px rgba(0, 0, 0, 0.08); }
    
    /* HEADER & PILLS */
    .card-header { padding: 16px 20px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
    .meta-pill { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; margin-right: 6px; }
    .assignee-pill { background-color: #f1f5f9; color: #475569; }
    .cost-pill { background-color: #ecfdf5; color: #059669; letter-spacing: 0.5px; }
    
    /* BUTTON STYLING */
    .stButton button { 
        border-radius: 6px; 
        border: 1px solid #e2e8f0; 
        padding: 2px 8px;
        font-size: 12px;
    }
    .stButton button:hover {
        border-color: #cbd5e1;
        background-color: #f1f5f9;
    }
    
    /* EDIT FORM STYLING */
    .edit-box {
        background-color: #fffbeb;
        border: 2px solid #fcd34d;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
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
            "Notes": "Need to confirm headcount with Finance first.",
            "Status": False
        }
    ])

if 'archived_tasks' not in st.session_state:
    st.session_state.archived_tasks = pd.DataFrame(columns=list(st.session_state.budget_tasks.columns) + ['Archived At'])

if 'Notes' not in st.session_state.budget_tasks.columns:
    st.session_state.budget_tasks['Notes'] = ""

if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None

# --- 3. HELPER FUNCTIONS ---

def normalize_department(input_str):
    if not isinstance(input_str, str): return "💰 Finance"
    input_clean = input_str.lower().strip()
    for key in DEPT_COLORS.keys():
        if key == input_str: return key
    for key in DEPT_COLORS.keys():
        if input_clean in key.lower(): return key
    return "💰 Finance"

def send_slack_summary(count, total_value):
    if not SLACK_WEBHOOK_URL: return
    payload = {
        "text": f"📥 *Bulk Import:* {count} items added (${total_value:,.2f})",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"📥 *Bulk Import Successful*\n{count} new line items have been added to the board."}},
            {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Total Items:*\n{count}"}, {"type": "mrkdwn", "text": f"*Total Value:*\n${total_value:,.2f}"}]}
        ]
    }
    try: requests.post(SLACK_WEBHOOK_URL, json=payload)
    except: pass

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

def complete_and_archive(index):
    """
    Moves the task at 'index' from budget_tasks to archived_tasks immediately.
    """
    # 1. Get the row
    row = st.session_state.budget_tasks.iloc[index].copy()
    
    # 2. Add Timestamp
    row['Archived At'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    row['Status'] = True # Ensure it's marked done
    
    # 3. Add to Archive DataFrame
    st.session_state.archived_tasks = pd.concat(
        [st.session_state.archived_tasks, pd.DataFrame([row])], 
        ignore_index=True
    )
    
    # 4. Remove from Active DataFrame
    st.session_state.budget_tasks = st.session_state.budget_tasks.drop(index).reset_index(drop=True)
    
    # 5. Clear Edit Mode if we just archived the item being edited
    if st.session_state.editing_index == index:
        st.session_state.editing_index = None
        
    # 6. User Feedback
    st.toast("✅ Task Completed & Archived!", icon="🎉")

def delete_task(index):
    if st.session_state.editing_index == index:
        st.session_state.editing_index = None
    st.session_state.budget_tasks = st.session_state.budget_tasks.drop(index).reset_index(drop=True)

# --- 4. TOP BANNER ---
total_spend = st.session_state.budget_tasks["Cost"].sum()
formatted_spend = f"${total_spend:,.2f}"

st.markdown(f"""
<div class="budget-banner">
    <div style="display: flex; align-items: center; gap: 24px;">
        <div style="background: rgba(255,255,255,0.15); padding: 16px; border-radius: 16px; backdrop-filter: blur(5px);">
            <span style="font-size: 40px;">🏦</span>
        </div>
        <div>
            <h1 style="color: white; margin: 0; font-size: 26px; font-weight: 700;">Budget Master 2026</h1>
            <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 15px;">Tracking {len(st.session_state.budget_tasks)} line items across departments</p>
        </div>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; font-weight: 600;">Projected Spend</div>
        <div style="font-size: 36px; font-weight: 800; color: white; letter-spacing: -1px;">{formatted_spend}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 5. EDIT MODE ---
if st.session_state.editing_index is not None:
    idx = st.session_state.editing_index
    if idx in st.session_state.budget_tasks.index:
        row_to_edit = st.session_state.budget_tasks.iloc[idx]
        
        st.markdown('<div class="edit-box">', unsafe_allow_html=True)
        st.subheader(f"✏️ Move or Edit: {row_to_edit['Task']}")
        
        with st.form("edit_mode_form"):
            col_e1, col_e2, col_e3 = st.columns(3)
            
            # Row 1 Inputs
            e_task = col_e1.text_input("Task Name", value=row_to_edit['Task'])
            
            current_dept_idx = list(DEPT_COLORS.keys()).index(row_to_edit['Department']) if row_to_edit['Department'] in DEPT_COLORS else 0
            e_dept = col_e2.selectbox("📂 Department (Move)", list(DEPT_COLORS.keys()), index=current_dept_idx)
            
            current_assignee_idx = TEAM[1:].index(row_to_edit['Assignee']) if row_to_edit['Assignee'] in TEAM[1:] else 0
            e_assignee = col_e3.selectbox("Assignee", TEAM[1:], index=current_assignee_idx)

            # Row 2 Inputs
            col_e4, col_e5 = st.columns(2)
            e_cost = col_e4.number_input("Cost ($)", value=float(row_to_edit['Cost']), min_value=0.0)
            e_date = col_e5.date_input("Due Date", value=pd.to_datetime(row_to_edit['Due Date']))
            
            # Row 3 Notes
            current_notes = str(row_to_edit['Notes']) if pd.notna(row_to_edit.get('Notes')) else ""
            e_notes = st.text_area("📝 Notes / Comments", value=current_notes)
            
            submitted = st.form_submit_button("💾 Save Changes")
            
            if submitted:
                st.session_state.budget_tasks.at[idx, 'Task'] = e_task
                st.session_state.budget_tasks.at[idx, 'Department'] = e_dept
                st.session_state.budget_tasks.at[idx, 'Assignee'] = e_assignee
                st.session_state.budget_tasks.at[idx, 'Cost'] = e_cost
                st.session_state.budget_tasks.at[idx, 'Due Date'] = e_date
                st.session_state.budget_tasks.at[idx, 'Notes'] = e_notes
                
                st.session_state.editing_index = None
                st.success("Task updated!")
                st.rerun()

        if st.button("Cancel"):
            st.session_state.editing_index = None
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.subheader("📥 Bulk Import")
    template_df = pd.DataFrame([{"Task": "Sample Item", "Department": "Marketing", "Assignee": "Alex", "Cost": 1000, "Due Date": "2026-01-30", "Notes": "Optional info"}])
    csv_template = template_df.to_csv(index=False).encode('utf-8')
    st.download_button("📄 Download Excel Template", data=csv_template, file_name="budget_template.csv", mime="text/csv")
    
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx'])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'): df_upload = pd.read_csv(uploaded_file)
            else: df_upload = pd.read_excel(uploaded_file)
            
            if 'Task' not in df_upload.columns:
                st.error("File is missing 'Task' column.")
            else:
                if st.button(f"Process {len(df_upload)} rows"):
                    new_rows = []
                    total_import_val = 0
                    for index, row in df_upload.iterrows():
                        matched_dept = normalize_department(row.get('Department', 'Finance'))
                        try: d_date = pd.to_datetime(row.get('Due Date', datetime.now()))
                        except: d_date = datetime.now() + timedelta(days=30)
                        try: cost_val = float(str(row.get('Cost', 0)).replace('$','').replace(',',''))
                        except: cost_val = 0.0
                        
                        note_val = str(row.get('Notes', ""))
                        if note_val == "nan": note_val = ""

                        new_rows.append({
                            "Task": str(row['Task']), 
                            "Department": matched_dept, 
                            "Assignee": str(row.get('Assignee', 'Team')), 
                            "Due Date": d_date, 
                            "Cost": cost_val, 
                            "Notes": note_val,
                            "Status": False
                        })
                        total_import_val += cost_val

                    st.session_state.budget_tasks = pd.concat([pd.DataFrame(new_rows), st.session_state.budget_tasks], ignore_index=True)
                    if SLACK_WEBHOOK_URL: send_slack_summary(len(new_rows), total_import_val)
                    st.success("Import Successful!")
                    st.rerun()
        except Exception as e: st.error(f"Error: {e}")

    st.markdown("---")
    st.subheader("➕ Single Entry")
    with st.form("add_budget_form", clear_on_submit=True):
        new_task = st.text_input("Line Item Name")
        new_dept = st.selectbox("Department", list(DEPT_COLORS.keys()))
        new_assignee = st.selectbox("Assignee", TEAM[1:])
        new_cost = st.number_input("Est. Cost ($)", min_value=0.0, step=100.0)
        new_date = st.date_input("Deadline", value=datetime.now() + timedelta(days=7))
        new_notes = st.text_area("Notes (Optional)", height=80)
        
        if st.form_submit_button("Add to Board"):
            new_entry = {
                "Task": new_task, "Department": new_dept, 
                "Assignee": new_assignee, "Due Date": pd.to_datetime(new_date), 
                "Cost": new_cost, "Notes": new_notes, "Status": False
            }
            st.session_state.budget_tasks = pd.concat([pd.DataFrame([new_entry]), st.session_state.budget_tasks], ignore_index=True)
            if SLACK_WEBHOOK_URL: send_slack_alert(new_task, new_dept, new_cost, new_assignee)
            st.rerun()

# --- 7. MODERN GRID LAYOUT ---
grid_cols = st.columns(3)

for i, (dept_name, dept_color) in enumerate(DEPT_COLORS.items()):
    col_idx = i % 3
    with grid_cols[col_idx]:
        dept_tasks = st.session_state.budget_tasks[st.session_state.budget_tasks["Department"] == dept_name]
        dept_total = dept_tasks["Cost"].sum()
        
        header_bg = f"{dept_color}15" 
        
        st.markdown(f"""
        <div class="kanban-card">
            <div class="card-header" style="background-color: {header_bg};">
                <span style="font-weight: 700; color: {dept_color}; font-size: 14px;">{dept_name}</span>
                <span style="font-size: 12px; font-weight: 700; color: {dept_color}; opacity: 0.9;">${dept_total:,.0f}</span>
            </div>
        """, unsafe_allow_html=True)
        
        if dept_tasks.empty:
            st.markdown("<div style='padding: 30px; text-align: center; color: #cbd5e1; font-size: 13px;'>No requests</div>", unsafe_allow_html=True)
        else:
            for idx, row in dept_tasks.iterrows():
                # Columns: Check | Text | Nudge | Edit | Delete
                c1, c2, c3, c4, c5 = st.columns([0.08, 0.58, 0.1, 0.1, 0.1])
                
                # CHECKBOX -> AUTO ARCHIVE
                # We use the 'complete_and_archive' function on change
                c1.checkbox(
                    "", 
                    value=False, # Always False initially because if it were True, it would be archived
                    key=f"b_{idx}", 
                    on_change=complete_and_archive, 
                    args=(idx,)
                )
                
                t_style = "font-weight: 600; color: #334155;"
                cost_str = f"${row['Cost']:,.0f}" if row['Cost'] > 0 else "TBD"
                
                notes_html = ""
                if pd.notna(row.get('Notes')) and str(row['Notes']).strip() != "":
                    notes_html = f"<div style='font-size: 11px; color: #64748b; background: #f1f5f9; padding: 4px 8px; border-radius: 4px; margin-top: 6px; display:inline-block;'>📝 {row['Notes']}</div>"

                c2.markdown(f"""
                <div style="padding-top: 2px;">
                    <div style="{t_style} font-size: 14px; margin-bottom: 6px;">{row['Task']}</div>
                    <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 4px;">
                        <span class="meta-pill assignee-pill">👤 {row['Assignee']}</span>
                        <span class="meta-pill cost-pill">{cost_str}</span>
                    </div>
                    {notes_html}
                </div>
                """, unsafe_allow_html=True)
                
                # Nudge Button
                if c3.button("🔔", key=f"n_{idx}", help="Nudge on Slack"):
                     if SLACK_WEBHOOK_URL:
                        send_slack_alert(row['Task'], row['Department'], row['Cost'], row['Assignee'], is_reminder=True)
                        st.toast("Nudged!", icon="🔔")

                # Edit (Move) Button
                if c4.button("✏️", key=f"edit_{idx}", help="Edit/Move Task"):
                    st.session_state.editing_index = idx
                    st.rerun()

                # Delete Button
                if c5.button("🗑️", key=f"del_{idx}", help="Delete Item"):
                    delete_task(idx)
                    st.rerun()

                st.markdown("<div style='border-bottom: 1px solid #f8fafc; margin: 8px 0;'></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# --- 8. HISTORY SECTION (Bottom) ---
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("📜 Transaction History / Archived Tasks"):
    if st.session_state.archived_tasks.empty:
        st.info("No archived tasks yet.")
    else:
        st.dataframe(
            st.session_state.archived_tasks, 
            use_container_width=True,
            column_config={
                "Status": None, # Hide status since they are all done
                "Cost": st.column_config.NumberColumn(format="$%.2f")
            }
        )
