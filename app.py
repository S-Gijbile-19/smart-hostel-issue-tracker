import streamlit as st
import pandas as pd
import os
from datetime import datetime
from database import (
    authenticate_user, add_issue, get_all_issues, get_student_issues,
    update_status, create_student, add_lost_found, get_lost_found,
    update_lost_found_status, add_announcement, get_announcements,
    get_visible_issues_for_student, get_public_issues_for_analytics,
    get_duplicates_for_issue, merge_issues
)

def color_status(val):
    if val in ["Lost"]:
        return "background-color: #ffe6e6; color: black;"
    elif val in ["Found"]:
        return "background-color: #e6ffe6; color: black;"
    elif val in ["Claimed", "Returned"]:
        return "background-color: #e6f0ff; color: black;"
    return ""

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
    dynamic_cols = ISSUE_COLUMNS.copy()
    if actual_width > len(dynamic_cols):
        for i in range(len(dynamic_cols), actual_width):
            dynamic_cols.append(f"Extra_{i}")
    return pd.DataFrame(issues_data, columns=dynamic_cols[:actual_width])

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
            
    st.divider()
    col1, col2, col3 = st.columns(3)
    features = [
        ("📌 Tracking", "No more paper logs. Every issue is tracked live."),
        ("💡 Role-Based", "Custom dashboards for Students and Management."),
        ("📊 Analytics", "Data-driven insights into hostel maintenance.")
    ]
    for col, (title, desc) in zip([col1, col2, col3], features):
        col.markdown(f'<div class="card"><h4>{title}</h4><p style="color:{sub_text}">{desc}</p></div>', unsafe_allow_html=True)
       # --- ROLE SECTION ---
    
    st.divider()
    st.subheader("User Experience")
    
    left, right = st.columns(2)
    
    with left:
        st.markdown(f"""
            <div style="background-color: {secondary_bg}; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #0284c7;">
                <h4 style="margin-top:0;">For Students</h4>
                <ul style="color: {sub_text};">
                    <li>Instant photo-based issue reporting</li>
                    <li>Real-time status tracking (Reported to Resolved)</li>
                    <li>Access to public hostel announcements</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown(f"""
            <div style="background-color: {secondary_bg}; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #22c55e;">
                <h4 style="margin-top:0;">For Management</h4>
                <ul style="color: {sub_text};">
                    <li>Direct caretaker assignment tools</li>
                    <li>Automated resolution time tracking</li>
                    <li>Data-driven maintenance planning</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    # --- FOOTER ---
    from datetime import datetime
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

# This ensures "username" and "role" are available globally for the tabs below
username = st.session_state.username
role = st.session_state.role
# --- SIDEBAR LOGOUT ---
st.sidebar.success(f"User: {st.session_state.username} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# --- TABS ---
tabs = st.tabs(["🛠 Issues", "🏷 Lost & Found", "📢 Announcements"])

# ================= ISSUES TAB =================
with tabs[0]:
    role = st.session_state.role
    user = st.session_state.username

    if role == "Student":
        st.header("Report New Issue")
        with st.form("report_form", clear_on_submit=True):
            cat = st.selectbox("Category", ["Plumbing", "Electrical", "Internet", "Other"])
            pri = st.select_slider("Priority", options=["Low", "Medium", "High", "Emergency"])
            desc = st.text_area("Description")
            vis = st.radio("Visibility", ["Private", "Public"], horizontal=True)
            if st.form_submit_button("Submit"):
                add_issue(user, cat, pri, desc, visibility=vis)
                st.success("Reported!")
        
        st.divider()
        st.subheader("My Reports")
        df = get_safe_df(get_visible_issues_for_student(user))
        st.dataframe(df[["ID", "Category", "Priority", "Status", "Created At"]], use_container_width=True)

    elif role == "Management":
        st.header("🛠 Management Console")
        issues_data = get_all_issues()
        df = get_safe_df(issues_data)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total", len(df))
        m2.metric("Open", len(df[df["Status"] != "Resolved"]))
        m3.metric("Resolved", len(df[df["Status"] == "Resolved"]))

        for _, row in df.iterrows():
            with st.expander(f"Issue #{row['ID']} - {row['Category']} ({row['Status']})"):
                st.write(f"**From:** {row['Student']} | **Room:** {row['Room']}")
                st.info(f"**Description:** {row['Description']}")
                
                # Update Status
                new_status = st.selectbox("Status", ["Reported", "Assigned", "In Progress", "Resolved"], 
                                         index=["Reported", "Assigned", "In Progress", "Resolved"].index(row['Status']),
                                         key=f"st_{row['ID']}")
                caretaker = st.text_input("Caretaker", value=row['Assigned To'] or "", key=f"ct_{row['ID']}")
                
                # Merge Logic
                if pd.isna(row['Parent ID']):
                    other_ids = df[df["ID"] != row["ID"]]["ID"].tolist()
                    parent = st.selectbox("Merge as duplicate of:", [None] + other_ids, key=f"p_{row['ID']}")
                    if parent and st.button("Merge Now", key=f"btn_{row['ID']}"):
                        merge_issues(parent, row['ID'])
                        st.rerun()
                else:
                    st.warning(f"Duplicate of #{int(row['Parent ID'])}")

                if st.button("Save Changes", key=f"sv_{row['ID']}", type="primary"):
                    update_status(row['ID'], new_status, caretaker)
                    st.rerun()

# ================= LOST & FOUND TAB =================
with tabs[1]:
    st.header("🏷 Lost & Found Portal")
    if role == "Student":
        st.subheader("Report Lost/Found Item")
        item_name = st.text_input("Item Name")
        category = st.selectbox(
            "Category",
            ["Electronics", "Books", "ID Cards", "Clothes", "Miscellaneous"],
            key="lf_cat"
        )
        description = st.text_area("Description (optional)", key="lf_desc")
        location = st.text_input("Location", key="lf_loc")
        status = st.selectbox("Status", ["Lost", "Found"], key="lf_status")
        image_file = st.file_uploader("Upload Image (optional)", type=["jpg","png","jpeg"])

        if st.button("Submit Lost/Found Item"):
            if image_file:
                os.makedirs("lf_uploads", exist_ok=True)
                image_path = f"lf_uploads/{username}_{image_file.name}"
                with open(image_path, "wb") as f:
                    f.write(image_file.getbuffer())
            else:
                image_path = None

            add_lost_found(username, role, item_name, category, description, location, status,image_path)
            st.success(f"{status} item reported successfully!")

        st.subheader("📌 View Lost & Found Items")
        items = get_lost_found()
        if items:
            df = pd.DataFrame(
                items,
                columns=["ID","Student","Role","Item Name","Category","Description","Location","Date","Status","Image Path"]
            )
            # Apply color to Status column
            st.dataframe(df.style.applymap(color_status, subset=["Status"]), use_container_width=True)
        else:
            st.info("No lost or found items reported yet.")

            st.subheader("🖼️ Item Images")
 # Optional: preview images (if you store paths in database)
            
            for item in items:
                if len(item) > 9 and item[9]:
                    st.markdown(f"**{item[3]} ({item[8]})**")
                    st.image(item[9], width=200)

            else:
                 st.info("No lost or found items reported yet.")


    # -------------------- MANAGEMENT VIEW --------------------
    elif role == "Management":
        st.subheader("All Lost & Found Reports")
        items = get_lost_found()
        if items:
            df = pd.DataFrame(
                items,
                columns=["ID","Student","Role","Item Name","Category","Description","Location","Date","Status","Image Path"]
            )
            st.dataframe(df.style.applymap(color_status, subset=["Status"]), use_container_width=True)

            # -------------------- IMAGE PREVIEW --------------------
            st.subheader("🖼️ Item Images")
            for item in items:
                if item[9]:
                    st.markdown(f"**{item[3]} ({item[8]})**")  # Item name + status
                    st.image(item[9], width=200)

                    
            st.subheader("Update Lost & Found Status")
            item_ids = df["ID"].tolist()
            selected_id = st.selectbox("Select Item ID", item_ids, key="lf_select_id")
            new_status = st.selectbox("New Status", ["Lost","Found","Returned","Claimed"], key="lf_new_status")
            if st.button("Update Status for Selected Item"):
                update_lost_found_status(selected_id, new_status)
                st.success("Status updated!")
        else:
            st.info("No lost or found items reported yet.")



# ================= ANNOUNCEMENTS TAB =================
with tabs[2]:
    st.header("📢 Official Announcements")
    if role == "Management":
        st.subheader("Post New Announcement")
        title = st.text_input("Title")
        message = st.text_area("Message")
        hostel = st.text_input("Hostel/Wing")
        block = st.text_input("Block/Wing (optional)")
        target_role = st.selectbox("Target Role", ["Student", "Management", "All"])

        if st.button("Post Announcement"):
            add_announcement(title, message, hostel, block, target_role)
            st.success("Announcement posted!")

    st.subheader("View Announcements")
    announcements = get_announcements(role=role)  # you can also filter by hostel/block if needed

    if announcements:
        df = pd.DataFrame(
            announcements,
            columns=["ID", "Title", "Message", "Hostel", "Block", "Role", "Created At"]
        )
        st.dataframe(df[["Title", "Message", "Hostel", "Block", "Role", "Created At"]], use_container_width=True)
    else:
        st.info("No announcements yet.")