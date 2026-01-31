import streamlit as st
import pandas as pd
import os

from database import (
    authenticate_user,
    add_issue,
    get_all_issues,
    get_student_issues,
    update_status,
    create_student,
    add_lost_found,
    get_lost_found,
    update_lost_found_status,
    add_announcement,
    get_announcements,
    get_visible_issues_for_student,
    datetime,
    get_public_issues_for_analytics,
    get_duplicates_for_issue,
    merge_issues
)

def color_status(val):
    if val in ["Lost"]:
        return "background-color: #ffe6e6"
    elif val in ["Found"]:
        return "background-color: #e6ffe6"
    elif val in ["Claimed", "Returned"]:
        return "background-color: #e6f0ff"
    return ""


# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Smart Hostel System", layout="wide")

#UI style
# 1. Setup the Toggle in the Sidebar
with st.sidebar:
    st.markdown("###  Appearance")
    dark_mode = st.toggle("Dark Mode", value=False)
    st.divider()

# 2. Define Professional Palettes
st.set_page_config(layout="wide")
if dark_mode:
    # --- DARK MODE PALETTE (Deep Slate/Navy) ---
    primary_bg = "#0f172a"      # Deep Navy
    secondary_bg = "#1e293b"    # Slate Navy
    sidebar_bg = "#020617"      # Near Black
    text_color = "#dee7f1"      # Ghost White
    sub_text = "#e9f2f0"        # Muted Slate
    card_bg = "#2b6fdd"
    border_color = "#334155"
else:
    # --- LIGHT MODE PALETTE (Clean SaaS) ---
    primary_bg = "#f8fafc"      # Sky White
    secondary_bg = "#ffffff"    # Pure White
    sidebar_bg = "#1e293b"      # Deep Slate (Kept dark for professional contrast)
    text_color = "#0f172a"      # Dark Navy
    sub_text = "#64748b"        # Muted Gray
    card_bg = "#ffffff"
    border_color = "#e2e8f0"

# 3. Inject the Dynamic CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* Main App Background */
    .stApp {{
        background-color: {primary_bg};
        color: {text_color};
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        border-right: 1px solid {border_color};
    }}

    /* Sidebar Text */
    section[data-testid="stSidebar"] .stText, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p {{
        color: #f1f5f9 !important;
    }}

    /* Headers */
    h1, h2, h3 {{
        color: {text_color} !important;
        font-weight: 700 !important;
    }}

    /* Professional Cards & Metrics */
    div[data-testid="stMetric"], .card {{
        background-color: {card_bg} !important;
        border: 1px solid {border_color} !important;
        padding: 1.25rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: {text_color} !important;
    }}

    /* Metric Label Fix */
    div[data-testid="stMetricLabel"] > div {{
        color: {sub_text} !important;
    }}

    /* Buttons */
    .stButton>button {{
        width: 100%;
        border-radius: 8px !important;
        background-color: #0284c7 !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }}

    /* Expander Styling */
    .streamlit-expanderHeader {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
    }}

    /* Input Fields */
    input, select, textarea {{
        background-color: {secondary_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
    }}
    
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.show_login = False

# ---------------- LANDING PAGE ----------------
def landing_page():
    # --- HERO SECTION ---
    st.markdown(f"""
        <div style="text-align: center; padding: 2rem 0rem;">
            <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">🏠 SmartHostel</h1>
            <p style="font-size: 1.2rem; color: {sub_text}; max-width: 700px; margin: 0 auto;">
                The modern standard for hostel operations. Streamline reporting, 
                automate assignments, and improve student living standards.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Big CTA Button
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        if st.button("Get Started", use_container_width=True, type="primary"):
            st.session_state.show_login = True
            st.rerun()

    st.write("---")

    # --- FEATURE GRID ---
    st.markdown("### 🛠️ Platform Capabilities")
    col1, col2, col3 = st.columns(3)

    # Using the 'card' style we defined earlier
    with col1:
        st.markdown(f"""
            <div class="card">
                <h4>📌 Centralized Tracking</h4>
                <p style="color: {sub_text}; font-size: 0.9rem;">
                    Say goodbye to scattered WhatsApp messages and paper logs. 
                    Every issue is tracked from report to resolution.
                </p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="card">
                <h4>💡 Role-Based Logic</h4>
                <p style="color: {sub_text}; font-size: 0.9rem;">
                    Customized dashboards for students to report and management 
                    to assign tasks with accountability.
                </p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="card">
                <h4>📊 Live Analytics</h4>
                <p style="color: {sub_text}; font-size: 0.9rem;">
                    Real-time insights into hostel density, response times, 
                    and frequent issue categories.
                </p>
            </div>
        """, unsafe_allow_html=True)

    st.write("---")

    # --- ROLE SECTION ---
    st.subheader("👥 User Experience")
    
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
    col1, col2 = st.columns([1, 5])

    with col1:
        if st.button("← Back"):
            st.session_state.show_login = False
            st.rerun()

    with col2:
        st.title("Smart Hostel System Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.role = user[0]
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid username or password")


# ---------------- DASHBOARD ROUTER ----------------
#def dashboard():
   #role = st.session_state.role
# ---- LOGIN / ROLE FETCH ----
role = st.session_state.get("role")

def student_dashboard():
    st.subheader("🎓 Student Dashboard")

def admin_dashboard():
    st.subheader("🛠️ Management Dashboard")
    # issues list, status update, etc


# ---------------- APP FLOW ----------------
if not st.session_state.logged_in:
    if not st.session_state.show_login:
        landing_page()
    else:
        login_page()
    st.stop()


# ---------------- SIDEBAR ----------------
role = st.session_state.role
username = st.session_state.username

st.sidebar.success(f"Logged in as {username} ({role})")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.show_login = False
    st.rerun()

# ---------------- DASHBOARD ----------------
#dashboard()


# ---------------- TABS ----------------
tabs = st.tabs(["🛠 Issue Tracker", "🏷 Lost & Found" ,"📢 Announcements" ])

# ===================== ISSUE TRACKER =====================


with tabs[0]:
# ===================== ISSUE TRACKER DASHBOARD =====================

 # ==================== DASHBOARD ====================

 if role == "Student":
    st.header("Student Dashboard - Issues")

    with st.container(border=True):
     st.subheader("📩 Report an Issue")

    category = st.selectbox(
        "Issue Category",
        ["Plumbing", "Electrical", "Cleanliness", "Internet", "Furniture", "Other"]
    )
    priority = st.selectbox("⚡ Priority Level", ["Low", "Medium", "High", "Emergency"])

    description = st.text_area("Describe the issue")

    image = st.file_uploader("Upload image (optional)", type=["jpg", "png", "jpeg"])

    visibility = st.selectbox(
        "Issue Visibility",
        ["Private", "Public"],
        help="Public issues are visible to all students"
    )

    if st.button("Submit Issue"):
        if description.strip() == "":
            st.warning("Please enter a description")
        else:
            if image:
                os.makedirs("uploads", exist_ok=True)
                image_path = f"uploads/{username}_{image.name}"
                with open(image_path, "wb") as f:
                    f.write(image.getbuffer())
            else:
                image_path = None

            add_issue(username, category, priority, description, image_path, visibility)
            st.success("Issue reported successfully!")
    
            st.divider()
    st.subheader("My Issues")

    issues = get_visible_issues_for_student(username)

    if not issues:
        st.info("No issues reported yet")
    else:
        # Columns exactly match DB (20 columns)
        df = pd.DataFrame(
            issues,
            columns=[
                "ID","Student","Category","Priority","Description","Status",
                "Assigned To","Remarks","Created At","Image Path","Visibility",
                "Hostel","Block","Room","Updated At","Reported At","Assigned At",
                "In Progress At","Resolved At"
            ]
        )

        st.dataframe(
            df[["ID","Student","Hostel","Block","Room","Category","Priority","Description","Status","Assigned To","Remarks","Created At"]],
            use_container_width=True
        )

    #st.write("🔍 ROLE CHECK (TOP):", role)
        
# ------------------- MANAGEMENT DASHBOARD -------------------
 elif role == "Management":
    st.header("🛠️ Management Dashboard - Issues")
    
    # Fetch all issues
    issues = get_all_issues()

    if not issues:
        st.info("No issues reported yet")
    else:
        STATUS_FLOW = ["Reported", "Assigned", "In Progress", "Resolved", "Closed"]

        # Create DataFrame with all 19 columns
        df = pd.DataFrame(
            issues,
            columns=[
                "ID", "Student", "Category", "Priority", "Description",
                "Status", "Assigned To", "Remarks", "Created At", "Image Path",
                "Visibility", "Hostel", "Block", "Room", "Updated At",
                "Reported At", "Assigned At", "In Progress At", "Resolved At","Parent ID"
            ]
        )

        # Optional Metrics at top
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Issues", len(df))
        col2.metric("Pending", len(df[df["Status"].isin(["Reported", "Assigned", "In Progress"])]))
        col3.metric("Resolved", len(df[df["Status"] == "Resolved"]))

        st.divider()

        # List each issue in an expander
        for issue in issues:
            with st.expander(f"Issue #{issue[0]} | {issue[2]} | {issue[3]} | {issue[5]}"):
                st.write(f"""
                👤 Student: {issue[1]}
                🏠 Hostel: {issue[11]}
                🧱 Block: {issue[12]}
                🚪 Room: {issue[13]}
                🗂 Category: {issue[2]}
                ⚡ Priority: {issue[3]}
                📝 Description: {issue[4]}
                """)

                # Show uploaded image
                if issue[9]:
                    st.image(issue[9], caption="Uploaded Image", width=300)

                # Assign caretaker/team
                caretaker = st.text_input(
                    "Assign to (Caretaker / Team)",
                    value=issue[6] if issue[6] else "",
                    key=f"mgmt_assign_{issue[0]}_{issue[5]}"

                )

    if issue[10]:
        st.warning(f"This is a duplicate of Issue # {issue[10]}")

    else:
        # Get other issues to merge (exclude current and already resolved)
        other_issues = df[df["ID"] != issue[0]]
        duplicate_target = st.selectbox(
            "Is this a duplicate of another issue?",
            options=[None] + other_issues["ID"].tolist(),
            format_func=lambda x: f"Issue #{x}" if x else "Select Parent Issue",
            key=f"merge_select_{issue[0]}"
        )

        if duplicate_target:
            if st.button(f"Merge #{issue[0]} into #{duplicate_target}", key=f"merge_btn_{issue[0]}"):
                merge_issues(duplicate_target, issue[0])
                st.success("Issues merged successfully!")
                st.rerun()
    # Display secondary reporters (if this is a parent)
    secondary_reporters = get_duplicates_for_issue(issue[0])
    if secondary_reporters:
        st.info(f"👥 Also reported by: {', '.join(secondary_reporters)}")           
                
                
                # Update status
        new_status = st.selectbox(
                    "Update Status",
                    STATUS_FLOW,
                    index=STATUS_FLOW.index(issue[5]),
                    key=f"mgmt_status_{issue[0]}_{issue[5]}"

                )

        if st.button("Save Update", key=f"btn_{issue[0]}"):
                    update_status(issue[0], new_status, caretaker)
                    st.success("Issue updated successfully")
                    st.rerun()
        st.divider()

  

# ---------------- MANAGEMENT ANALYTICS DASHBOARD ----------------
    
        st.subheader("📊 Management Analytics Dashboard")
        st.caption("Public issues only")

        public_issues = get_public_issues_for_analytics()

        if not public_issues:
            st.info("No public issues reported yet for analytics.")
        else:
            df_a = pd.DataFrame(
                public_issues,
                columns=[
                "Category",
                "Hostel",
                "Block",
                "Status",
                "Created At",
                "Assigned At",
                "Resolved At"
        ]
    )

    # Convert to datetime
            df_a["Created At"] = pd.to_datetime(df_a["Created At"])
            df_a["Assigned At"] = pd.to_datetime(df_a["Assigned At"])
            df_a["Resolved At"] = pd.to_datetime(df_a["Resolved At"])

    # ---------- METRICS ----------
            df_a["Response_Hours"] = (
                df_a["Assigned At"] - df_a["Created At"]
            ).dt.total_seconds() / 3600

            df_a["Resolution_Hours"] = (
                df_a["Resolved At"] - df_a["Created At"]
            ).dt.total_seconds() / 3600

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Avg Response Time (hrs)",
                f"{df_a['Response_Hours'].dropna().mean():.2f}"
                 if not df_a["Response_Hours"].dropna().empty else "N/A"
            )

            c2.metric(
                "Avg Resolution Time (hrs)",
                f"{df_a['Resolution_Hours'].dropna().mean():.2f}"
                if not df_a["Resolution_Hours"].dropna().empty else "N/A"
            )

            pending = len(df_a[df_a["Status"] != "Resolved"])
            resolved = len(df_a[df_a["Status"] == "Resolved"])

            c3.metric("Pending vs Resolved", f"{pending} / {resolved}")

    # ---------- CHARTS ----------
            st.subheader("🏷 Most Frequently Reported Issue Categories")
            st.bar_chart(df_a["Category"].value_counts())

            st.subheader("🏠 Hostel / Block-wise Issue Density")
            df_a["Hostel_Block"] = df_a["Hostel"] + " - " + df_a["Block"]
            st.bar_chart(df_a["Hostel_Block"].value_counts())

            st.subheader("📈 Issue Status Distribution")
            st.bar_chart(df_a["Status"].value_counts())



# ===================== LOST & FOUND =====================
with tabs[1]:
    st.header("🏷 Lost & Found")

    # -------------------- STUDENT VIEW --------------------
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


with tabs[2]:
    st.header("📢 Hostel Announcements")

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
