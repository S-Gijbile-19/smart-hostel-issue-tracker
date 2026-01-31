import streamlit as st
import pandas as pd
import os
from datetime import datetime
from database import (
    authenticate_user, add_issue, get_all_issues, 
    update_status, create_student, add_lost_found, get_lost_found,
    update_lost_found_status, add_announcement, get_announcements,
    get_visible_issues_for_student, merge_issues
)

# ---------------- GLOBAL CONSTANTS ----------------
ISSUE_COLUMNS = [
    "ID", "Student", "Category", "Priority", "Description",
    "Status", "Assigned To", "Remarks", "Created At", "Image Path",
    "Visibility", "Hostel", "Block", "Room", "Updated At",
    "Reported At", "Assigned At", "In Progress At", "Resolved At", 
    "Closed At", "Parent ID"
]

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Smart Hostel System", layout="wide", page_icon="🏠")

# ---------------- THEME & UI CUSTOMIZATION ----------------
with st.sidebar:
    st.markdown("### Appearance")
    dark_mode = st.toggle("Dark Mode", value=False)
    st.divider()

if dark_mode:
    primary_bg, secondary_bg, sidebar_bg = "#0f172a", "#1e293b", "#020617"
    text_color, sub_text, card_bg, border_color = "#dee7f1", "#e9f2f0", "#1e293b", "#334155"
else:
    primary_bg, secondary_bg, sidebar_bg = "#f8fafc", "#ffffff", "#1e293b"
    text_color, sub_text, card_bg, border_color = "#0f172a", "#666D69", "#ffffff", "#7A7678"

st.markdown(f"""
<style>
    .stApp {{ background-color: {primary_bg}; color: {text_color}; }}
    section[data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; }}
    .card {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    .stButton>button {{ border-radius: 8px !important; font-weight: 600 !important; }}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "role": None, "username": None, "show_login": False})

# ---------------- HELPER FUNCTIONS ----------------
def get_safe_df(issues_data):
    if not issues_data:
        return pd.DataFrame(columns=ISSUE_COLUMNS)
    actual_width = len(issues_data[0])
    return pd.DataFrame(issues_data, columns=ISSUE_COLUMNS[:actual_width])

def color_status(val):
    colors = {
        "Lost": "background-color: #ffe6e6; color: black;",
        "Found": "background-color: #e6ffe6; color: black;",
        "Claimed": "background-color: #e6f0ff; color: black;",
        "Returned": "background-color: #e6f0ff; color: black;"
    }
    return colors.get(val, "")

# ---------------- LANDING PAGE ----------------
def landing_page():
    st.markdown(f"""
        <div style="text-align: center; padding: 3rem 0;">
            <h1 style="font-size: 3.5rem;">Smart Hostel</h1>
            <p style="font-size: 1.2rem; color: {sub_text}; max-width: 700px; margin: 0 auto;">
                The modern standard for hostel operations. Streamline reporting, automate assignments, and improve student living.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        if st.button("🚀 Get Started", use_container_width=True, type="primary"):
            st.session_state.show_login = True
            st.rerun()
    
    # --- FEATURE CARDS ---
    col1, col2, col3 = st.columns(3)
    features = [
        ("📌 Tracking", "No more paper logs. Every issue is tracked live from report to resolution."),
        ("💡 Role-Based", "Custom dashboards tailored for both Student needs and Management oversight."),
        ("📊 Analytics", "Gain data-driven insights to improve long-term hostel maintenance.")
    ]
    for col, (title, desc) in zip([col1, col2, col3], features):
        col.markdown(f"""
            <div class="card">
                <h4 style="margin-top:0;">{title}</h4>
                <p style="color:{sub_text}; font-size:0.9rem;">{desc}</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("User Experience")
    
    # --- ROLE INFO CARDS ---
    left, right = st.columns(2)
    with left:
        st.markdown(f"""
            <div style="background-color: {secondary_bg}; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #0284c7; height: 180px;">
                <h4 style="margin-top:0;">For Students</h4>
                <ul style="color: {sub_text}; font-size: 0.9rem;">
                    <li>Instant photo-based issue reporting</li>
                    <li>Real-time status tracking</li>
                    <li>Access to hostel announcements</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown(f"""
            <div style="background-color: {secondary_bg}; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #22c55e; height: 180px;">
                <h4 style="margin-top:0;">For Management</h4>
                <ul style="color: {sub_text}; font-size: 0.9rem;">
                    <li>Direct caretaker assignment tools</li>
                    <li>Automated resolution timestamps</li>
                    <li>Data-driven maintenance planning</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    # --- FOOTER ---
    current_year = datetime.now().year
    st.markdown(f"""
        <div style="text-align: center; margin-top: 4rem; padding: 2rem; border-top: 1px solid {border_color};">
            <p style="color: {sub_text}; font-size: 0.8rem;">
                © {current_year} SmartHostel Tracker • Built for Efficiency
            </p>
        </div>
    """, unsafe_allow_html=True)

# ---------------- LOGIN PAGE ----------------
def login_page():
    if st.button("← Back"):
        st.session_state.show_login = False
        st.rerun()
    st.title("Secure Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
        auth = authenticate_user(user, pwd)
        if auth:
            st.session_state.update({"logged_in": True, "role": auth[0], "username": user})
            st.rerun()
        else:
            st.error("Invalid Credentials")

# ---------------- MAIN APP LOGIC ----------------
if not st.session_state.logged_in:
    if not st.session_state.show_login: landing_page()
    else: login_page()
    st.stop()

username = st.session_state.username
role = st.session_state.role

st.sidebar.success(f"User: {username} ({role})")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

tabs = st.tabs(["🛠 Issues", "🏷 Lost & Found", "📢 Announcements"])

# ================= ISSUES TAB =================
with tabs[0]:
    if role == "Student":
        st.header("Report New Issue")
        with st.form("report_form", clear_on_submit=True):
            cat = st.selectbox("Category", ["Plumbing", "Electrical", "Internet", "Other"])
            pri = st.select_slider("Priority", options=["Low", "Medium", "High", "Emergency"])
            desc = st.text_area("Description")
            image = st.file_uploader("Upload image (optional)", type=["jpg", "png", "jpeg"])
            vis = st.radio("Visibility", ["Private", "Public"], horizontal=True)
            
            if st.form_submit_button("Submit"):
                if not desc.strip():
                    st.warning("Please enter a description")
                else:
                    image_path = None
                    if image:
                        os.makedirs("uploads", exist_ok=True)
                        image_path = f"uploads/{username}_{image.name}"
                        with open(image_path, "wb") as f:
                            f.write(image.getbuffer())
                    
                    add_issue(username, cat, pri, desc, image_path=image_path, visibility=vis)
                    st.success("Issue Reported!")
                    st.rerun()
        
        st.divider()
        st.subheader("My View")
        df = get_safe_df(get_visible_issues_for_student(username))
        st.dataframe(df[["ID", "Category", "Priority", "Status", "Created At", "Visibility"]], use_container_width=True)

    elif role == "Management":
        st.header("🛠 Management Console")
        df = get_safe_df(get_all_issues())
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total", len(df))
        m2.metric("Open", len(df[df["Status"] != "Resolved"]))
        m3.metric("Resolved", len(df[df["Status"] == "Resolved"]))

        for _, row in df.iterrows():
            with st.expander(f"Issue #{row['ID']} - {row['Category']} ({row['Status']})"):
                st.write(f"**From:** {row['Student']} | **Room:** {row['Room']}")
                st.info(f"**Description:** {row['Description']}")
                
                if row['Image Path'] and os.path.exists(row['Image Path']):
                    st.image(row['Image Path'], width=300)

                col_a, col_b = st.columns(2)
                with col_a:
                    new_status = st.selectbox("Update Status", ["Reported", "Assigned", "In Progress", "Resolved"], 
                                         index=["Reported", "Assigned", "In Progress", "Resolved"].index(row['Status']),
                                         key=f"st_{row['ID']}")
                    caretaker = st.text_input("Assign Caretaker", value=row['Assigned To'] or "", key=f"ct_{row['ID']}")
                
                with col_b:
                    if pd.isna(row['Parent ID']):
                        other_ids = df[df["ID"] != row["ID"]]["ID"].tolist()
                        parent = st.selectbox("Mark as Duplicate of:", [None] + other_ids, key=f"p_{row['ID']}")
                        if parent and st.button("Link & Merge", key=f"btn_{row['ID']}"):
                            merge_issues(parent, row['ID'])
                            st.rerun()
                    else:
                        st.warning(f"Duplicate of Issue #{int(row['Parent ID'])}")

                if st.button("Save Updates", key=f"sv_{row['ID']}", type="primary"):
                    update_status(row['ID'], new_status, caretaker)
                    st.rerun()

# ================= LOST & FOUND TAB =================
with tabs[1]:
    st.header("🏷 Lost & Found Portal")
    if role == "Student":
        with st.expander("➕ Report Item"):
            item_name = st.text_input("Item Name")
            category = st.selectbox("Category", ["Electronics", "Books", "ID Cards", "Clothes", "Misc"], key="lf_cat")
            description = st.text_area("Description", key="lf_desc")
            location = st.text_input("Last Seen/Found Location", key="lf_loc")
            status = st.selectbox("Status", ["Lost", "Found"], key="lf_status")
            image_file = st.file_uploader("Item Image", type=["jpg","png","jpeg"], key="lf_img")

            if st.button("Post Item"):
                lf_path = None
                if image_file:
                    os.makedirs("lf_uploads", exist_ok=True)
                    lf_path = f"lf_uploads/{username}_{image_file.name}"
                    with open(lf_path, "wb") as f:
                        f.write(image_file.getbuffer())
                add_lost_found(username, role, item_name, category, description, location, status, lf_path)
                st.success("Posted!")
                st.rerun()

    items = get_lost_found()
    if items:
        df_lf = pd.DataFrame(items, columns=["ID","User","Role","Item","Category","Desc","Loc","Date","Status","Image"])
        st.dataframe(df_lf.style.applymap(color_status, subset=["Status"]), use_container_width=True)
        
        st.subheader("🖼️ Gallery")
        cols = st.columns(4)
        for i, item in enumerate(items):
            if item[9] and os.path.exists(item[9]):
                with cols[i % 4]:
                    st.image(item[9], caption=f"{item[3]} ({item[8]})")

        if role == "Management":
            st.divider()
            st.subheader("Admin: Update Status")
            sel_id = st.selectbox("Select Item ID", df_lf["ID"].tolist())
            st_new = st.selectbox("New Status", ["Lost","Found","Returned","Claimed"])
            if st.button("Update LF Status"):
                update_lost_found_status(sel_id, st_new)
                st.rerun()
    else:
        st.info("No items reported.")

# ================= ANNOUNCEMENTS TAB =================
with tabs[2]:
    st.header("📢 Announcements")
    if role == "Management":
        with st.expander("📢 Post New"):
            t = st.text_input("Title")
            m = st.text_area("Message")
            h = st.text_input("Hostel Filter (Optional)")
            target = st.selectbox("Target", ["Student", "Management", "All"])
            if st.button("Broadcast"):
                add_announcement(t, m, h, "All", target)
                st.success("Broadcasted!")
                st.rerun()

    ann = get_announcements(role=role)
    for a in ann:
        st.markdown(f"""
        <div class="card">
            <h4>{a[1]}</h4>
            <p>{a[2]}</p>
            <small style="color:gray;">{a[6]} | Target: {a[5]}</small>
        </div>
        """, unsafe_allow_html=True)
