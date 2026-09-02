import sqlite3
import os
from werkzeug.security import generate_password_hash

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "campus_complaint.db")

# Make sure database folder exists
os.makedirs(DATABASE_DIR, exist_ok=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    conn = get_db_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # STUDENTS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            department TEXT,
            year TEXT,
            division TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # ADMINS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # DEPARTMENTS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    """)

    # --------------------------------------------------------
    # COMPLAINTS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,

            title TEXT NOT NULL,
            description TEXT NOT NULL,

            category TEXT NOT NULL,

            department_id INTEGER,

            location TEXT,

            priority TEXT DEFAULT 'Medium',

            status TEXT DEFAULT 'New',

            assigned_to INTEGER,

            resolution TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,

            FOREIGN KEY (student_id)
                REFERENCES students(id)
                ON DELETE CASCADE,

            FOREIGN KEY (department_id)
                REFERENCES departments(id)
                ON DELETE SET NULL,

            FOREIGN KEY (assigned_to)
                REFERENCES admins(id)
                ON DELETE SET NULL
        )
    """)

    # --------------------------------------------------------
    # COMPLAINT SUPPORT / UPVOTES TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_support (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            complaint_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(complaint_id, student_id),

            FOREIGN KEY (complaint_id)
                REFERENCES complaints(id)
                ON DELETE CASCADE,

            FOREIGN KEY (student_id)
                REFERENCES students(id)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # COMPLAINT STATUS HISTORY
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            complaint_id INTEGER NOT NULL,

            old_status TEXT,
            new_status TEXT NOT NULL,

            changed_by INTEGER,

            note TEXT,

            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (complaint_id)
                REFERENCES complaints(id)
                ON DELETE CASCADE,

            FOREIGN KEY (changed_by)
                REFERENCES admins(id)
                ON DELETE SET NULL
        )
    """)

    # --------------------------------------------------------
    # NOTIFICATIONS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,

            complaint_id INTEGER,

            message TEXT NOT NULL,

            is_read INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (student_id)
                REFERENCES students(id)
                ON DELETE CASCADE,

            FOREIGN KEY (complaint_id)
                REFERENCES complaints(id)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # DEFAULT DEPARTMENTS
    # --------------------------------------------------------

    departments = [
        ("Academics", "Academic related complaints"),
        ("Examination", "Examination and result related complaints"),
        ("Hostel", "Hostel related complaints"),
        ("Library", "Library related complaints"),
        ("Canteen", "Food and canteen related complaints"),
        ("Transport", "College transport related complaints"),
        ("Infrastructure", "Building, classroom and infrastructure complaints"),
        ("IT / Computer", "Computer, Wi-Fi and technical complaints"),
        ("Cleanliness", "Cleaning and hygiene related complaints"),
        ("Other", "Other college related complaints")
    ]

    for name, description in departments:
        cursor.execute("""
            INSERT OR IGNORE INTO departments (name, description)
            VALUES (?, ?)
        """, (name, description))

    # --------------------------------------------------------
    # DEFAULT ADMIN ACCOUNT
    # --------------------------------------------------------

    admin_email = "admin@campus.com"

    cursor.execute(
        "SELECT id FROM admins WHERE email = ?",
        (admin_email,)
    )

    existing_admin = cursor.fetchone()

    if existing_admin is None:

        hashed_password = generate_password_hash("admin123")

        cursor.execute("""
            INSERT INTO admins
            (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "System Administrator",
            admin_email,
            hashed_password,
            "super_admin"
        ))

    # Save changes
    conn.commit()

    conn.close()

    print("========================================")
    print("Campus Complaint Database Initialized")
    print("========================================")
    print(f"Database: {DATABASE_PATH}")
    print("Default Admin:")
    print("Email    : admin@campus.com")
    print("Password : admin123")
    print("========================================")


# ============================================================
# RUN DATABASE INITIALIZATION
# ============================================================

if __name__ == "__main__":
    init_db()