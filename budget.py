import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Budget 2026 Tracker", page_icon="💰", layout="wide")

# --- SECRETS SETUP ---
# We grab the URL from Streamlit's secure vault
try:
    SLACK_WEBHOOK_URL = st.secrets["slack_webhook"]
except FileNotFoundError:
    st.error("🚨 Slack Webhook not found. Please add it to Streamlit Secrets.")
    SLACK_WEBHOOK_URL = "http://hooks.slack.com/services/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"
except KeyError:
    st.error("🚨 Key 'slack_webhook' not found in Secrets.")
    SLACK_WEBHOOK_URL = ""

# --- TEAM CONFIGURATION WITH SLACK IDs ---
SLACK_TEAM_IDS = {
    "Tate": "U0H8U5B7D",
    "Yuval": "UH8MRM8CB",
    "Shane": "U79A2AHLZ",
    "Shy": "USAC60WB1",
    "Garth": "U51A7EBJ7",
    "Agata": "U07PA7N7Y9L",
    "Kike": "UQJG96F3L",
    "Karim": "U07TJM3404D",
    "Simon": "U065152B5A5",
    "Jess": "U06MURH8R17",
    "Kathy": "U05AS678C8Y",
    "Thomas": "U06CVDPFAPK"
}

TEAM = ["All"] + list(SLACK_TEAM_IDS.keys())

# Department Configuration
DEPT_COLORS = {
    "🎧 Customer Care": "#f97316", "💻 Development": "#3b82f6", "💰 Finance": "#10b981",
    "📢 Marketing": "#ec4899", "🖥️ IT Operation": "#64748b", "📈 Data & Rev Op": "#8b5cf6",
    "🚀 Product": "#6366f1", "💼 Sales & Success": "#0ea5e9", "⚖️ Legal": "#d97706",
    "👔 Leadership": "#111827", "💜 People & Culture": "#06b6d4"
}

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .main { background-color: #f8fafc; }
    h1, h2, h3, h4, p, div, span { font-family: 'Inter', sans-serif; }
    .budget-banner {
        background: linear-gradient(120deg, #0f172a 0%, #334155 100%);
        padding: 2.5rem; border-radius: 20px; color: white; margin-bottom: 30px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); display: flex; align-items: center; justify-content: space-between;
    }
    .kanban-card {
        background-color: white; border-radius: 16px; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02); margin-bottom: 24px;
        overflow: hidden; transition: all 0.2s ease;
    }
    .kanban-card:hover { transform: translateY(-4px); box-shadow: 0 12px 16px -4px rgba(0, 0, 0, 0.08); }
    .card-header { padding: 16px 20px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
    .meta-pill { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; margin-right: 6px; }
    .assignee-pill { background-color: #f1f5f9; color: #475569; }
    .cost-pill { background-color: #ecfdf5; color: #059669; letter-spacing: 0.5px; }
    .stButton button { border-radius: 6px; border: 1px solid #e2e8f0; padding: 2px 8px; font-size: 12px; }
    .edit-box { background-color: #fffbeb; border: 2px solid #fcd34d; padding: 20px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# --- DATA & HELPER FUNCTIONS ---

if 'budget_tasks' not in st.session_state:
    st.session_state.budget_tasks = pd.DataFrame([{"Task": "Q1 Hiring Plan Review", "Department": "💜 People & Culture", "Assignee": "Kathy", "Due Date": datetime.now() + timedelta(days=5), "Cost": 2500.0, "Notes": "Check headcount", "Status": False}])

if 'archived_tasks' not in st.session_state:
    st.session_state.archived_tasks = pd.DataFrame(columns=list(st.session_state.budget_tasks.columns) + ['Archived At'])
if 'Notes' not in st.session_state.budget_tasks.columns: st.session_state.budget_tasks['Notes'] = ""
if 'editing_index' not in st.session_state: st.session_state.editing_index = None

def normalize_department(input_str):
    if not isinstance(input_str, str): return "💰 Finance"
    input_clean = input_str.lower().strip()
    for key in DEPT_COLORS.keys():
        if key == input_str: return key
    for key in DEPT_COLORS.keys():
        if input_clean in key.lower(): return key
    return "💰 Finance"

def get_slack_mention(name):
    slack_id = SLACK_TEAM_IDS.get(name, "")
    if slack_id and slack_id.startswith("U"): return f"<@{slack_id}>"
    return name

def send_slack_test():
    if not SLACK_WEBHOOK_URL: return False, "No Webhook URL found in Secrets."
    payload = {"text": "🔔 *Slack Integration Test*\nConnection successful! 🚀"}
    try:
        r = requests.post(SLACK_WEBHOOK_URL, json=payload)
        return (True, "Success!") if r.status_code == 200 else (False, f"Error: {r.status_code}")
    except Exception as e: return False, str(e)

def send_slack_summary(count, total_value):
    if not SLACK_WEBHOOK_URL: return
    payload = {"text": f"📥 *Bulk Import:* {count} items added (${total_value:,.2f})"}
    try: requests.post(SLACK_WEBHOOK_URL, json=payload)
    except: pass

def send_slack_alert(task, dept, cost, assignee, is_reminder=False):
    if not SLACK_WEBHOOK_URL: return
    formatted_cost = f"${cost:,.2f}"
    assignee_tag = get_slack_mention(assignee)
    if is_reminder: title, emoji, pretext = "Item Reminder", "🔔", f"Hey {assignee_tag}, update needed:"
    else: title, emoji, pretext = "New Request", "💸", "New budget item added:"
    payload = {
        "text": f"{emoji} {title}: {task}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {title}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": pretext}},
            {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Dept:* {dept}"}, {"type": "mrkdwn", "text": f"*Cost:* {formatted_cost}"}, {"type": "mrkdwn", "text": f"*Task:* {task}"}, {"type": "mrkdwn", "text": f"*Who:* {assignee}"}]}
        ]
    }
    try: requests.post(SLACK_WEBHOOK_URL, json=payload)
    except: pass

def complete_and_archive(index):
    row = st.session_state.budget_tasks.iloc[index].copy()
    row['Archived At'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    row['Status'] = True 
    st.session_state.archived_tasks = pd.concat([st.session_state.archived_tasks, pd.DataFrame([row])], ignore_index=True)
    st.session_state.budget_tasks = st.session_state.budget_tasks.drop(index).reset_index(drop=True)
    if st.session_state.editing_index == index: st.session_state.editing_index = None
    st.toast("✅ Task Completed & Archived!", icon="🎉")

def delete_task(index):
    if st.session_state.editing_index == index: st.session_state.editing_index = None
    st.session_state.budget_tasks = st.session_state.budget_tasks.drop(index).reset_index(drop=True)

# --- UI LAYOUT ---
total_spend = st.session_state.budget_tasks["Cost"].sum()
st.markdown(f"""<div class="budget-banner"><div style="display:flex;align-items:center;gap:24px;"><span style="font-size:40px;">🏦</span><div><h1 style="color:white;margin:0;font-size:26px;">Budget Master 2026</h1></div></div><div style="text-align:right;"><div style="font-size:13px;">Projected Spend</div><div style="font-size:36px;font-weight:800;">${total_spend:,.2f}</div></div></div>""", unsafe_allow_html=True)

if st.session_state.editing_index is not None:
    idx = st.session_state.editing_index
    if idx in st.session_state.budget_tasks.index:
        row = st.session_state.budget_tasks.iloc[idx]
        st.markdown('<div class="edit-box">', unsafe_allow_html=True)
        st.subheader(f"✏️ Move or Edit: {row['Task']}")
        with st.form("edit_mode_form"):
            c1, c2, c3 = st.columns(3)
            e_task = c1.text_input("Task Name", row['Task'])
            e_dept = c2.selectbox("📂 Department", list(DEPT_COLORS.keys()), list(DEPT_COLORS.keys()).index(row['Department']) if row['Department'] in DEPT_COLORS else 0)
            e_assignee = c3.selectbox("Assignee", TEAM[1:], TEAM[1:].index(row['Assignee']) if row['Assignee'] in TEAM[1:] else 0)
            c4, c5 = st.columns(2)
            e_cost = c4.number_input("Cost", float(row['Cost']))
            e_date = c5.date_input("Due", pd.to_datetime(row['Due Date']))
            e_notes = st.text_area("Notes", str(row['Notes']) if pd.notna(row['Notes']) else "")
            if st.form_submit_button("💾 Save"):
                st.session_state.budget_tasks.loc[idx] = [e_task, e_dept, e_assignee, e_date, e_cost, e_notes, False]
                st.session_state.editing_index = None
                st.rerun()
        if st.button("Cancel"):
            st.session_state.editing_index = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with st.sidebar:
    st.subheader("🔧 Configuration")
    if st.button("🔔 Test Slack Connection"):
        ok, msg = send_slack_test()
        if ok: st.success(msg)
        else: st.error(msg)
    st.markdown("---")
    st.subheader("📥 Bulk Import")
    template_df = pd.DataFrame([{"Task": "Sample", "Department": "Marketing", "Assignee": "Alex", "Cost": 1000, "Due Date": "2026-01-30", "Notes": "Info"}])
    st.download_button("📄 Template", template_df.to_csv(index=False).encode('utf-8'), "budget_template.csv", "text/csv")
    up = st.file_uploader("Upload CSV/Excel", type=['csv','xlsx'])
    if up and st.button(f"Process"):
        try:
            df = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
            new_rows = []
            tot = 0
            for _, r in df.iterrows():
                cost = float(str(r.get('Cost',0)).replace('$','').replace(',',''))
                new_rows.append({"Task": str(r['Task']), "Department": normalize_department(r.get('Department')), "Assignee": str(r.get('Assignee','Team')), "Due Date": pd.to_datetime(r.get('Due Date', datetime.now())), "Cost": cost, "Notes": str(r.get('Notes','')), "Status": False})
                tot += cost
            st.session_state.budget_tasks = pd.concat([pd.DataFrame(new_rows), st.session_state.budget_tasks], ignore_index=True)
            send_slack_summary(len(new_rows), tot)
            st.success("Imported!")
            st.rerun()
        except Exception as e: st.error(e)
    st.markdown("---")
    st.subheader("➕ Single Entry")
    with st.form("add"):
        nt = st.text_input("Item")
        nd = st.selectbox("Dept", list(DEPT_COLORS.keys()))
        na = st.selectbox("Who", TEAM[1:])
        nc = st.number_input("Cost")
        dd = st.date_input("Due")
        nn = st.text_area("Notes")
        if st.form_submit_button("Add"):
            st.session_state.budget_tasks = pd.concat([pd.DataFrame([{"Task":nt,"Department":nd,"Assignee":na,"Due Date":pd.to_datetime(dd),"Cost":nc,"Notes":nn,"Status":False}]), st.session_state.budget_tasks], ignore_index=True)
            send_slack_alert(nt, nd, nc, na)
            st.rerun()

cols = st.columns(3)
for i, (d_name, d_col) in enumerate(DEPT_COLORS.items()):
    with cols[i%3]:
        d_tasks = st.session_state.budget_tasks[st.session_state.budget_tasks["Department"] == d_name]
        bg = f"{d_col}15"
        st.markdown(f"""<div class="kanban-card"><div class="card-header" style="background-color:{bg};"><span style="font-weight:700;color:{d_col};">{d_name}</span><span style="font-size:12px;font-weight:700;color:{d_col};">${d_tasks['Cost'].sum():,.0f}</span></div>""", unsafe_allow_html=True)
        if d_tasks.empty: st.markdown("<div style='padding:30px;text-align:center;color:#cbd5e1;font-size:13px;'>No requests</div>", unsafe_allow_html=True)
        else:
            for idx, row in d_tasks.iterrows():
                c1, c2, c3, c4, c5 = st.columns([0.1, 0.56, 0.1, 0.1, 0.1])
                c1.checkbox("", False, key=f"b_{idx}", on_change=complete_and_archive, args=(idx,))
                notes_html = f"<div style='font-size:10px;color:#64748b;background:#f1f5f9;padding:2px 6px;border-radius:4px;display:inline-block;margin-top:4px;'>📝 {row['Notes']}</div>" if pd.notna(row['Notes']) and str(row['Notes']) else ""
                c2.markdown(f"""<div style="padding-top:2px;"><div style="font-weight:600;color:#334155;font-size:14px;">{row['Task']}</div><div style="display:flex;gap:4px;"><span class="meta-pill assignee-pill">👤 {row['Assignee']}</span><span class="meta-pill cost-pill">${row['Cost']:,.0f}</span></div>{notes_html}</div>""", unsafe_allow_html=True)
                if c3.button("🔔", key=f"n_{idx}"): 
                    send_slack_alert(row['Task'], row['Department'], row['Cost'], row['Assignee'], True)
                    st.toast("Nudged!", icon="🔔")
                if c4.button("✏️", key=f"e_{idx}"):
                    st.session_state.editing_index = idx
                    st.rerun()
                if c5.button("🗑️", key=f"d_{idx}"):
                    delete_task(idx)
                    st.rerun()
                st.markdown("<hr style='margin:5px 0;border-top:1px solid #f8fafc;'>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📜 Transaction History"):
    st.dataframe(st.session_state.archived_tasks, use_container_width=True)
