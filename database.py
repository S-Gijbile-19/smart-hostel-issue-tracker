import sqlite3
import datetime

# ---------------- DATABASE CONNECTION ----------------
conn = sqlite3.connect("issues.db", check_same_thread=False)
cursor = conn.cursor()

# ---------------- INITIALIZATION & MIGRATIONS ----------------
def initialize_db():
    # Users Table
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

    # Issues Table
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
        visibility TEXT DEFAULT 'Public',
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

    # Lost & Found Table
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

    # Announcements Table
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

def run_migrations():
    """Ensures old databases are updated with new columns automatically."""
    cursor.execute("PRAGMA table_info(issues)")
    cols = [col[1] for col in cursor.fetchall()]
    new_cols = {
        "visibility": "TEXT DEFAULT 'Public'",
        "parent_id": "INTEGER DEFAULT NULL",
        "updated_at": "TIMESTAMP",
        "assigned_at": "TEXT",
        "resolved_at": "TEXT",
        "hostel": "TEXT",
        "block": "TEXT",
        "room": "TEXT"
    }
    for col_name, col_type in new_cols.items():
        if col_name not in cols:
            try:
                cursor.execute(f"ALTER TABLE issues ADD COLUMN {col_name} {col_type}")
            except: pass
    conn.commit()

initialize_db()
run_migrations()

# ---------------- AUTHENTICATION ----------------
def authenticate_user(username, password):
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    return cursor.fetchone()

def create_student(username, password="123", hostel="Girls Hostel", block="A", room="101"):
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role, hostel, block, room) VALUES (?, ?, 'Student', ?, ?, ?)", 
                   (username, password, hostel, block, room))
    conn.commit()

def create_default_admin():
    cursor.execute("SELECT * FROM users WHERE role='Management'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'Management')")
        conn.commit()

create_default_admin()
create_student("student1", "123")

# ---------------- ISSUES LOGIC ----------------
def add_issue(student, category, priority, description, image_path=None, visibility="Public"):
    cursor.execute("SELECT hostel, block, room FROM users WHERE username=?", (student,))
    res = cursor.fetchone()
    h, b, r = res if res else ("N/A", "N/A", "N/A")
    cursor.execute("""
        INSERT INTO issues (student, category, priority, description, status, visibility, hostel, block, room, image_path)
        VALUES (?, ?, ?, ?, 'Reported', ?, ?, ?, ?, ?)
    """, (student, category, priority, description, visibility, h, b, r, image_path))
    conn.commit()

def get_all_issues():
    cursor.execute("SELECT * FROM issues ORDER BY id DESC")
    return cursor.fetchall()

def get_visible_issues_for_student(student):
    cursor.execute("SELECT * FROM issues WHERE student=? OR visibility='Public' ORDER BY created_at DESC", (student,))
    return cursor.fetchall()

def update_status(issue_id, new_status, caretaker=None):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = "UPDATE issues SET status=?, updated_at=?"
    params = [new_status, now]
    if caretaker:
        query += ", assigned_to=?"; params.append(caretaker)
    if new_status == "Resolved":
        query += ", resolved_at=?"; params.append(now)
    query += " WHERE id=?"; params.append(issue_id)
    cursor.execute(query, tuple(params))
    conn.commit()

def merge_issues(parent_id, child_id):
    cursor.execute("UPDATE issues SET parent_id = ?, status = 'Duplicate' WHERE id = ?", (parent_id, child_id))
    conn.commit()

# ---------------- LOST & FOUND ----------------
def add_lost_found(name, role, item, cat, desc, loc, status, path):
    cursor.execute("""INSERT INTO lost_found (student_name, role, item_name, category, description, location, status, image_path)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (name, role, item, cat, desc, loc, status, path))
    conn.commit()

def get_lost_found():
    cursor.execute("SELECT * FROM lost_found ORDER BY date_reported DESC")
    return cursor.fetchall()

def update_lost_found_status(item_id, new_status):
    cursor.execute("UPDATE lost_found SET status=? WHERE id=?", (new_status, item_id))
    conn.commit()

# ---------------- ANNOUNCEMENTS & ANALYTICS ----------------
def add_announcement(title, msg, hostel, block, role):
    cursor.execute("INSERT INTO announcements (title, message, hostel, block, role) VALUES (?, ?, ?, ?, ?)", (title, msg, hostel, block, role))
    conn.commit()

def get_announcements(role=None):
    cursor.execute("SELECT * FROM announcements WHERE role=? OR role='All' ORDER BY created_at DESC", (role,))
    return cursor.fetchall()

def get_public_issues_for_analytics():
    cursor.execute("SELECT category, hostel, block, status, created_at FROM issues WHERE visibility = 'Public'")
    return cursor.fetchall()
