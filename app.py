import streamlit as st
import pandas as pd
import os
from datetime import datetime
from database import (
    authenticate_user, add_issue, get_all_issues, update_status, 
    add_lost_found, get_lost_found, update_lost_found_status, 
    add_announcement, get_announcements, get_visible_issues_for_student, 
    merge_issues, get_public_issues_for_analytics
)

# ---------------- CONFIG & STYLES ----------------
st.set_page_config(page_title="Smart Hostel", layout="wide", page_icon="🏠")

ISSUE_COLUMNS = ["ID", "Student", "Category", "Priority", "Description", "Status", "Assigned To", "Remarks", "Created At", "Image Path", "Visibility", "Hostel", "Block", "Room", "Updated At", "Reported At", "Assigned At", "In Progress At", "Resolved At", "Closed At", "Parent ID"]

with st.sidebar:
    st.markdown("### Appearance")
    dark = st.toggle("Dark Mode", value=False)
    st.divider()

bg, card, txt, border = ("#0f172a", "#1e293b", "#dee7f1", "#334155") if dark else ("#f8fafc", "#ffffff", "#0f172a", "#7A7678")
st.markdown(f"<style>.stApp {{ background-color: {bg}; color: {txt}; }} .card {{ background-color: {card}; border: 1px solid {border}; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; }}</style>", unsafe_allow_html=True)

# ---------------- STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "role": None, "username": None, "show_login": False})

def get_safe_df(data):
    if not data: return pd.DataFrame(columns=ISSUE_COLUMNS)
    return pd.DataFrame(data, columns=ISSUE_COLUMNS[:len(data[0])])

# ---------------- PAGES ----------------
def landing_page():
    # --- HERO SECTION ---
    st.markdown(f"""
        <div style="text-align: center; padding: 3rem 0;">
            <h1 style="font-size: 3.5rem;">Smart Hostel</h1>
            <p style="font-size: 1.2rem; color: {txt}; max-width: 700px; margin: 0 auto; opacity: 0.8;">
                The modern standard for hostel operations. Streamline reporting, automate assignments, and improve student living with real-time data.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # --- LOGIN BUTTON ---
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        if st.button("🚀 Get Started", use_container_width=True, type="primary"):
            st.session_state.show_login = True
            st.rerun()
            
    st.divider()
    
    # --- FEATURE CARDS ---
    col1, col2, col3 = st.columns(3)
    features = [
        ("📌 Smart Tracking", "No more paper logs. Every issue is tracked live from report to resolution with timestamped logs."),
        ("💡 Role-Based Views", "Custom dashboards tailored for both Student needs and Management oversight in one unified app."),
        ("📊 Live Analytics", "Gain data-driven insights to identify recurring maintenance issues and improve hostel quality.")
    ]
    for col, (title, desc) in zip([col1, col2, col3], features):
        col.markdown(f"""
            <div class="card">
                <h4 style="margin-top:0; color: #0284c7;">{title}</h4>
                <p style="font-size:0.9rem; opacity: 0.9;">{desc}</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("Platform Experience")
    
    # --- ROLE INFO CARDS (The blue and green side-by-side cards) ---
    left, right = st.columns(2)
    with left:
        st.markdown(f"""
            <div style="background-color: {card}; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #0284c7; height: 180px; border-top: 1px solid {border}; border-right: 1px solid {border}; border-bottom: 1px solid {border};">
                <h4 style="margin-top:0;">For Students</h4>
                <ul style="font-size: 0.9rem; opacity: 0.8;">
                    <li>Instant photo-based issue reporting</li>
                    <li>Real-time status tracking & notifications</li>
                    <li>Community Lost & Found portal</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown(f"""
            <div style="background-color: {card}; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #22c55e; height: 180px; border-top: 1px solid {border}; border-right: 1px solid {border}; border-bottom: 1px solid {border};">
                <h4 style="margin-top:0;">For Management</h4>
                <ul style="font-size: 0.9rem; opacity: 0.8;">
                    <li>Direct caretaker assignment tools</li>
                    <li>Identify and merge duplicate reports</li>
                    <li>Data-driven maintenance planning</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    # --- FOOTER ---
    current_year = datetime.now().year
    st.markdown(f"""
        <div style="text-align: center; margin-top: 4rem; padding: 2rem; border-top: 1px solid {border};">
            <p style="font-size: 0.8rem; opacity: 0.6;">
                © {current_year} SmartHostel Maintenance Tracker • Built for Efficiency
            </p>
        </div>
    """, unsafe_allow_html=True)

def login_page():
    if st.button("← Back"): st.session_state.show_login = False; st.rerun()
    u = st.text_input("Username"); p = st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
        auth = authenticate_user(u, p)
        if auth: st.session_state.update({"logged_in": True, "role": auth[0], "username": u}); st.rerun()
        else: st.error("Invalid Credentials")

if not st.session_state.logged_in:
    landing_page() if not st.session_state.show_login else login_page()
    st.stop()

# ---------------- APP ----------------
st.sidebar.success(f"{st.session_state.username} ({st.session_state.role})")
if st.sidebar.button("Logout"): st.session_state.clear(); st.rerun()

tabs = st.tabs(["🛠 Issues", "🏷 Lost & Found", "📢 Announcements", "📊 Analytics"])

with tabs[0]: # ISSUES
    if st.session_state.role == "Student":
        with st.form("report"):
            cat = st.selectbox("Category", ["Plumbing", "Electrical", "Internet", "Other"])
            pri = st.select_slider("Priority", options=["Low", "Medium", "High", "Emergency"])
            desc = st.text_area("Description")
            img = st.file_uploader("Image", type=["jpg","png"])
            vis = st.radio("Visibility", ["Private", "Public"], horizontal=True)
            if st.form_submit_button("Submit"):
                path = None
                if img:
                    os.makedirs("uploads", exist_ok=True); path = f"uploads/{img.name}"
                    with open(path, "wb") as f: f.write(img.getbuffer())
                add_issue(st.session_state.username, cat, pri, desc, path, vis)
                st.success("Reported!"); st.rerun()
        st.dataframe(get_safe_df(get_visible_issues_for_student(st.session_state.username)), use_container_width=True)
    else:
        df = get_safe_df(get_all_issues())
        for _, r in df.iterrows():
            with st.expander(f"Issue #{r['ID']} - {r['Category']} ({r['Status']})"):
                st.write(r['Description'])
                if r['Image Path']: st.image(r['Image Path'], width=200)
                ns = st.selectbox("Status", ["Reported", "Assigned", "In Progress", "Resolved"], index=["Reported", "Assigned", "In Progress", "Resolved"].index(r['Status']), key=f"s{r['ID']}")
                ct = st.text_input("Caretaker", value=r['Assigned To'] or "", key=f"c{r['ID']}")
                if st.button("Update", key=f"u{r['ID']}"): update_status(r['ID'], ns, ct); st.rerun()

with tabs[1]: # LOST & FOUND
    if st.session_state.role == "Student":
        with st.expander("Report Item"):
            it = st.text_input("Item Name"); c = st.selectbox("Cat", ["Electronics", "Misc"])
            loc = st.text_input("Location"); s = st.selectbox("Status", ["Lost", "Found"])
            if st.button("Post"): add_lost_found(st.session_state.username, "Student", it, c, "", loc, s, None); st.rerun()
    items = get_lost_found()
    if items:
        st.dataframe(pd.DataFrame(items, columns=["ID","User","Role","Item","Category","Desc","Loc","Date","Status","Image"]), use_container_width=True)

with tabs[2]: # ANNOUNCEMENTS
    if st.session_state.role == "Management":
        with st.form("ann"):
            t = st.text_input("Title"); m = st.text_area("Message")
            if st.form_submit_button("Post"): add_announcement(t, m, "All", "All", "All"); st.rerun()
    for a in get_announcements(st.session_state.role):
        st.markdown(f"<div class='card'><h4>{a[1]}</h4><p>{a[2]}</p><small>{a[6]}</small></div>", unsafe_allow_html=True)

with tabs[3]: # ANALYTICS
    if st.session_state.role == "Management":
        st.header("📊 Hostel Maintenance Analytics")
        data = get_public_issues_for_analytics()
        
        if data:
            df_ana = pd.DataFrame(data, columns=["Category", "Hostel", "Block", "Status", "Date"])
            
            # Top level metrics
            m1, m2 = st.columns(2)
            m1.metric("Total Public Issues", len(df_ana))
            m2.metric("Most Active Hostel", df_ana["Hostel"].mode()[0] if not df_ana.empty else "N/A")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Issue Categories")
                st.bar_chart(df_ana["Category"].value_counts())
                
            with col2:
                st.subheader("Issues by Hostel")
                st.bar_chart(df_ana["Hostel"].value_counts())
                
            st.subheader("Maintenance Load by Block")
            # Create a pivot for a stacked area chart
            chart_data = df_ana.groupby(['Block', 'Category']).size().unstack().fillna(0)
            st.area_chart(chart_data)
        else:
            st.info("No public data available for analytics yet.")
    else:
        # What the student sees instead
        st.header("📊 Hostel Stats")
        st.info("Detailed maintenance analytics are restricted to Management.")
        
