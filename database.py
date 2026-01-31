import sqlite3
from datetime import datetime

# ---------------- DATABASE CONNECTION ----------------
conn = sqlite3.connect("issues.db", check_same_thread=False)
cursor = conn.cursor()

# ---- ADD MISSING TIMESTAMP COLUMNS SAFELY ----
def add_missing_issue_columns():
    columns = [
        "assigned_at",
        "in_progress_at",
        "resolved_at",
        "closed_at"
    ]

    for col in columns:
        try:
            cursor.execute(f"ALTER TABLE issues ADD COLUMN {col} TEXT")
        except:
            pass  # column already exists

    conn.commit()

add_missing_issue_columns()

def fix_issue_status_timestamp():
    try:
        cursor.execute("ALTER TABLE issues ADD COLUMN updated_at TIMESTAMP")
        conn.commit()
    except:
        pass  # column already exists

fix_issue_status_timestamp()

# ---------------- USERS TABLE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    hostel TEXT,
    block TEXT,
    room TEXT
)
""")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN hostel TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN block TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN room TEXT")
except:
    pass
conn.commit()

# ---------------- ISSUES TABLE ----------------
# ---------------- ISSUES TABLE (Corrected 21-Column Schema) ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    category TEXT,
    priority TEXT,
    description TEXT,
    status TEXT,
    assigned_to TEXT,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT,
    visibility TEXT,
    hostel TEXT,
    block TEXT,
    room TEXT,
    updated_at TIMESTAMP,
    reported_at TIMESTAMP,
    assigned_at TEXT,
    in_progress_at TEXT,
    resolved_at TEXT,
    closed_at TEXT,
    parent_id INTEGER DEFAULT NULL
)
""")
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS issue_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id INTEGER,
    old_status TEXT,
    new_status TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT
)
""")               



# ---------------- LOST & FOUND TABLE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS lost_found (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    role TEXT,
    item_name TEXT,
    category TEXT,
    description TEXT,
    location TEXT,
    date_reported TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT,
    image_path TEXT
)
""")

conn.commit()


# ---------------- ANNOUNCEMENTS TABLE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    message TEXT,
    hostel TEXT,
    block TEXT,
    role TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()



# ---------------- DEFAULT MANAGEMENT USER ----------------
def create_default_admin():
    cursor.execute("SELECT * FROM users WHERE role='Management'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "Management")
        )
        conn.commit()

create_default_admin()

# ---------------- AUTHENTICATION ----------------
def authenticate_user(username, password):
    cursor.execute(
        "SELECT role FROM users WHERE username=? AND password=?",
        (username, password)
    )
    return cursor.fetchone()

# ---------------- ADD ISSUE ----------------
def add_issue(student, category, priority, description, image_path=None, visibility="Public"):
    cursor.execute(
        "SELECT hostel, block, room FROM users WHERE username=?",
        (student,)
    )
    hostel, block, room = cursor.fetchone()

    cursor.execute("""
        INSERT INTO issues
        (student, category, priority, description, status,
         visibility, hostel, block, room, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student, category, priority, description,
        "Reported", visibility, hostel, block, room, image_path
    ))
    conn.commit()



# ---------------- GET ALL ISSUES (MANAGEMENT) ----------------
def get_all_issues():
    conn = sqlite3.connect("issues.db")
    cursor = conn.cursor()
    #cursor.execute("SELECT * FROM issues ORDER BY created_at DESC")
    cursor.execute("SELECT * FROM issues ORDER BY id DESC")
    data = cursor.fetchall()
    #rows = cursor.fetchall()
    conn.close()
    #return rows
    return data


# ---------------- GET STUDENT ISSUES ----------------
def get_student_issues(student):
    cursor.execute(
        "SELECT * FROM issues WHERE student=? ORDER BY created_at DESC",
        (student,)
    )
    return cursor.fetchall()


#Update Status
from datetime import datetime
# ---------------- UPDATE ISSUE STATUS WITH TIMESTAMPS ----------------
import datetime

def update_status(issue_id, new_status, caretaker=None):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Start building query and values
    query = "UPDATE issues SET status=?, "
    values = [new_status]

    # Update caretaker if provided
    if caretaker is not None:
        query += "assigned_to=?, "
        values.append(caretaker)

    # Update timestamps based on status
    if new_status == "Assigned":
        query += "assigned_at=?, "
        values.append(now)
    elif new_status == "In Progress":
        query += "in_progress_at=?, "
        values.append(now)
    elif new_status == "Resolved":
        query += "resolved_at=?, "
        values.append(now)

    # Always update updated_at
    query += "updated_at=? WHERE id=?"
    values.append(now)
    values.append(issue_id)

    cursor.execute(query, tuple(values))
    conn.commit()


def merge_issues(parent_id, child_id):
    """
    Links a duplicate issue to a parent issue and marks it as a duplicate.
    """
    conn = sqlite3.connect("issues.db") 
    cursor = conn.cursor()
    
    # 1. Update the child issue to point to the parent and set status
    cursor.execute("""
        UPDATE issues 
        SET parent_id = ?, status = 'Duplicate', remarks = ?
        WHERE id = ?
    """, (parent_id, f"Merged into Issue #{parent_id}", child_id))
    
    conn.commit()
    conn.close()

def get_duplicates_for_issue(parent_id):
    """
    Fetches all student names who reported a duplicate of this issue.
    """
    conn = sqlite3.connect("issues.db")
    cursor = conn.cursor()
    cursor.execute("SELECT student FROM issues WHERE parent_id = ?", (parent_id,))
    reporters = cursor.fetchall()
    conn.close()
    return [r[0] for r in reporters]


# ---------------- ASSIGN ISSUE ----------------
def assign_issue(issue_id, assignee):
    cursor.execute("""
        UPDATE issues 
        SET assigned_to=?, status=?
        WHERE id=?
    """, (assignee, "Assigned", issue_id))
    conn.commit()

def create_student(username, password="123"):
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, password, "Student")
    )
    conn.commit()



#Lost and Found table
# Add a new lost/found item
def add_lost_found(student_name, role, item_name, category, description, location, status,image_path):
    cursor.execute("""
    INSERT INTO lost_found 
    (student_name, role, item_name, category, description, location, date_reported, status,image_path)
    VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)
    """, (student_name, role, item_name, category, description, location, status,image_path))
    conn.commit()

# Fetch all lost/found items
def get_lost_found():
    cursor.execute("SELECT * FROM lost_found ORDER BY date_reported DESC")
    return cursor.fetchall()

# Update status of an item
def update_lost_found_status(item_id, new_status):
    cursor.execute("UPDATE lost_found SET status=? WHERE id=?", (new_status, item_id))
    conn.commit()



# Add announcement
def add_announcement(title, message, hostel, block, role):
    cursor.execute("""
        INSERT INTO announcements (title, message, hostel, block, role)
        VALUES (?, ?, ?, ?, ?)
    """, (title, message, hostel, block, role))
    conn.commit()

# Get announcements for user
def get_announcements(hostel=None, block=None, role=None):
    query = "SELECT * FROM announcements WHERE 1=1"
    params = []

    if hostel:
        query += " AND hostel=?"
        params.append(hostel)
    if block:
        query += " AND block=?"
        params.append(block)
    if role:
        query += " AND (role=? OR role='All')"
        params.append(role)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, tuple(params))
    return cursor.fetchall()

#visibility
def get_visible_issues_for_student(student):
    cursor.execute("""
        SELECT * FROM issues
        WHERE visibility='Public' OR student=?
        ORDER BY created_at DESC
    """, (student,))
    return cursor.fetchall()



cursor.execute("PRAGMA table_info(issues)")
columns = [col[1] for col in cursor.fetchall()]

if "visibility" not in columns:
    cursor.execute(
        "ALTER TABLE issues ADD COLUMN visibility TEXT DEFAULT 'Public'"
    )
    conn.commit()


#student create function
def create_student(
    username,
    password="123",
    hostel="Girls Hostel",
    block="A",
    room="101"
):
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role, hostel, block, room)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, password,"Student", hostel, block, room))
    conn.commit()

def get_user_profile(username):
    cursor.execute("""
        SELECT hostel, block, room
        FROM users
        WHERE username=?
    """, (username,))
    return cursor.fetchone()


create_student("student1", "123")
create_student("student2", "123")



def get_public_issues_for_analytics():
    conn = sqlite3.connect("issues.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            category,
            hostel,
            block,
            status,
            created_at,
            assigned_at,
            resolved_at
        FROM issues
        WHERE visibility = 'Public'
    """)

    data = cursor.fetchall()
    conn.close()
    return data

def ensure_parent_id_exists():
    import sqlite3
    conn = sqlite3.connect("issues.db")
    cursor = conn.cursor()
    try:
        # PRAGMA lets us see the current table structure
        cursor.execute("PRAGMA table_info(issues)")
        cols = [info[1] for info in cursor.fetchall()]
        if "parent_id" not in cols:
            cursor.execute("ALTER TABLE issues ADD COLUMN parent_id INTEGER DEFAULT NULL")
            conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

# Call this at the start of your script
ensure_parent_id_exists()