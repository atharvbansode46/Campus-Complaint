from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection, init_db
from ai_service import ask_gemini


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(__name__)

# Used for login sessions and flash messages
app.secret_key = "campus_complaint_secret_key_change_later"


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()


# ============================================================
# HOME ROUTE
# ============================================================

@app.route("/")
def home():

    # If already logged in
    if "user_id" in session:

        if session.get("user_type") == "admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("student_dashboard"))

    return redirect(url_for("login"))


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        student_id = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()
        division = request.form.get("division", "").strip()
        phone = request.form.get("phone", "").strip()

        # Basic validation
        if not student_id or not name or not email or not password:

            flash(
                "Please fill all required fields.",
                "error"
            )

            return redirect(url_for("register"))

        conn = get_db_connection()

        try:

            # Check whether student already exists
            existing_student = conn.execute(
                """
                SELECT id
                FROM students
                WHERE student_id = ? OR email = ?
                """,
                (student_id, email)
            ).fetchone()

            if existing_student:

                flash(
                    "Student ID or email already registered.",
                    "error"
                )

                return redirect(url_for("register"))

            # Hash password
            hashed_password = generate_password_hash(password)

            # Insert student
            conn.execute(
                """
                INSERT INTO students
                (
                    student_id,
                    name,
                    email,
                    password,
                    department,
                    year,
                    division,
                    phone
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    name,
                    email,
                    hashed_password,
                    department,
                    year,
                    division,
                    phone
                )
            )

            conn.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except Exception as e:

            conn.rollback()

            flash(
                f"Registration failed: {e}",
                "error"
            )

            return redirect(url_for("register"))

        finally:

            conn.close()

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:

            flash(
                "Please enter email and password.",
                "error"
            )

            return redirect(url_for("login"))

        conn = get_db_connection()

        # ----------------------------------------------------
        # CHECK ADMIN
        # ----------------------------------------------------

        admin = conn.execute(
            """
            SELECT *
            FROM admins
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if admin and check_password_hash(
            admin["password"],
            password
        ):

            session.clear()

            session["user_id"] = admin["id"]
            session["user_type"] = "admin"
            session["user_name"] = admin["name"]
            session["user_email"] = admin["email"]
            session["role"] = admin["role"]

            conn.close()

            return redirect(
                url_for("admin_dashboard")
            )

        # ----------------------------------------------------
        # CHECK STUDENT
        # ----------------------------------------------------

        student = conn.execute(
            """
            SELECT *
            FROM students
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()

        if student and check_password_hash(
            student["password"],
            password
        ):

            session.clear()

            session["user_id"] = student["id"]
            session["user_type"] = "student"
            session["user_name"] = student["name"]
            session["user_email"] = student["email"]
            session["student_id"] = student["student_id"]

            return redirect(
                url_for("student_dashboard")
            )

        flash(
            "Invalid email or password.",
            "error"
        )

        return redirect(url_for("login"))

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("login"))


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route("/dashboard")
def student_dashboard():

    if session.get("user_type") != "student":

        return redirect(url_for("login"))

    student_id = session["user_id"]

    conn = get_db_connection()

    # Get student's complaints
    complaints = conn.execute(
        """
        SELECT
            c.*,
            d.name AS department_name,

            (
                SELECT COUNT(*)
                FROM complaint_support cs
                WHERE cs.complaint_id = c.id
            ) AS support_count

        FROM complaints c

        LEFT JOIN departments d
            ON c.department_id = d.id

        WHERE c.student_id = ?

        ORDER BY c.created_at DESC
        """,
        (student_id,)
    ).fetchall()

    # Get notifications
    notifications = conn.execute(
        """
        SELECT *
        FROM notifications
        WHERE student_id = ?

        ORDER BY created_at DESC

        LIMIT 10
        """,
        (student_id,)
    ).fetchall()

    # Statistics
    total_complaints = len(complaints)

    resolved_complaints = sum(
        1
        for complaint in complaints
        if complaint["status"] == "Resolved"
        or complaint["status"] == "Closed"
    )

    pending_complaints = sum(
        1
        for complaint in complaints
        if complaint["status"] not in ["Resolved", "Closed"]
    )

    conn.close()

    return render_template(
        "student_dashboard.html",
        complaints=complaints,
        notifications=notifications,
        total_complaints=total_complaints,
        resolved_complaints=resolved_complaints,
        pending_complaints=pending_complaints
    )


# ============================================================
# SUBMIT COMPLAINT
# ============================================================

@app.route("/complaint/new", methods=["GET", "POST"])
def submit_complaint():

    if session.get("user_type") != "student":

        return redirect(url_for("login"))

    conn = get_db_connection()

    # Get departments for dropdown
    departments = conn.execute(
        """
        SELECT *
        FROM departments
        ORDER BY name
        """
    ).fetchall()

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        department_id = request.form.get("department_id", "").strip()
        location = request.form.get("location", "").strip()
        priority = request.form.get("priority", "Medium").strip()

        # Validation
        if not title or not description or not category:

            conn.close()

            flash(
                "Title, description and category are required.",
                "error"
            )

            return redirect(
                url_for("submit_complaint")
            )

        # ----------------------------------------------------
        # BASIC DUPLICATE DETECTION
        # ----------------------------------------------------

        duplicate = conn.execute(
            """
            SELECT id, title, status
            FROM complaints

            WHERE LOWER(title) = LOWER(?)

            AND status NOT IN ('Resolved', 'Closed')

            LIMIT 1
            """,
            (title,)
        ).fetchone()

        if duplicate:

            conn.close()

            flash(
                f"A similar complaint already exists "
                f"(Complaint #{duplicate['id']}). "
                f"You can support that complaint instead.",
                "error"
            )

            return redirect(
                url_for(
                    "complaint_details",
                    complaint_id=duplicate["id"]
                )
            )

        # ----------------------------------------------------
        # INSERT COMPLAINT
        # ----------------------------------------------------

        conn.execute(
    """
    INSERT INTO complaints
    (
        student_id,
        title,
        description,
        category,
        department_id,
        location,
        priority,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (
        session["user_id"],
        title,
        description,
        category,
        department_id if department_id else None,
        location,
        priority,
        "New"
    )
)

        conn.commit()

        # Get newly created complaint
        complaint = conn.execute(
            """
            SELECT id
            FROM complaints

            WHERE student_id = ?

            ORDER BY id DESC

            LIMIT 1
            """,
            (session["user_id"],)
        ).fetchone()

        complaint_id = complaint["id"]

        # Add initial status history
        conn.execute(
            """
            INSERT INTO complaint_status_history
            (
                complaint_id,
                old_status,
                new_status,
                changed_by,
                note
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                complaint_id,
                None,
                "New",
                None,
                "Complaint submitted by student."
            )
        )

        conn.commit()

        conn.close()

        flash(
            f"Complaint #{complaint_id} submitted successfully.",
            "success"
        )

        return redirect(
            url_for(
                "complaint_details",
                complaint_id=complaint_id
            )
        )

    conn.close()

    return render_template(
        "submit_complaints.html",
        departments=departments
    )


# ============================================================
# COMPLAINT DETAILS
# ============================================================

@app.route("/complaint/<int:complaint_id>")
def complaint_details(complaint_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()

    complaint = conn.execute(
        """
        SELECT
            c.*,

            s.name AS student_name,
            s.student_id AS student_number,
            s.email AS student_email,

            d.name AS department_name,

            a.name AS assigned_admin

        FROM complaints c

        JOIN students s
            ON c.student_id = s.id

        LEFT JOIN departments d
            ON c.department_id = d.id

        LEFT JOIN admins a
            ON c.assigned_to = a.id

        WHERE c.id = ?
        """,
        (complaint_id,)
    ).fetchone()

    if not complaint:

        conn.close()

        flash(
            "Complaint not found.",
            "error"
        )

        return redirect(url_for("student_dashboard"))

    # Security:
    # Student can only view their own complaint.
    if session.get("user_type") == "student":

        if complaint["student_id"] != session["user_id"]:

            conn.close()

            flash(
                "You are not authorized to view this complaint.",
                "error"
            )

            return redirect(
                url_for("student_dashboard")
            )

    # Support count
    support_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaint_support
        WHERE complaint_id = ?
        """,
        (complaint_id,)
    ).fetchone()[0]

    # Check whether current student supported it
    user_supported = False

    if session.get("user_type") == "student":

        supported = conn.execute(
            """
            SELECT id
            FROM complaint_support

            WHERE complaint_id = ?
            AND student_id = ?
            """,
            (
                complaint_id,
                session["user_id"]
            )
        ).fetchone()

        user_supported = supported is not None

    # Status history
    history = conn.execute(
        """
        SELECT
            h.*,
            a.name AS admin_name

        FROM complaint_status_history h

        LEFT JOIN admins a
            ON h.changed_by = a.id

        WHERE h.complaint_id = ?

        ORDER BY h.changed_at ASC
        """,
        (complaint_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "complaint_details.html",
        complaint=complaint,
        support_count=support_count,
        user_supported=user_supported,
        history=history
    )


# ============================================================
# SUPPORT / UPVOTE COMPLAINT
# ============================================================

@app.route(
    "/complaint/<int:complaint_id>/support",
    methods=["POST"]
)
def support_complaint(complaint_id):

    if session.get("user_type") != "student":

        return redirect(url_for("login"))

    student_id = session["user_id"]

    conn = get_db_connection()

    # Check complaint
    complaint = conn.execute(
        """
        SELECT *
        FROM complaints
        WHERE id = ?
        """,
        (complaint_id,)
    ).fetchone()

    if not complaint:

        conn.close()

        flash(
            "Complaint not found.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    # Student cannot support own complaint
    if complaint["student_id"] == student_id:

        conn.close()

        flash(
            "You cannot support your own complaint.",
            "error"
        )

        return redirect(
            url_for(
                "complaint_details",
                complaint_id=complaint_id
            )
        )

    # Check existing support
    existing_support = conn.execute(
        """
        SELECT id
        FROM complaint_support

        WHERE complaint_id = ?
        AND student_id = ?
        """,
        (
            complaint_id,
            student_id
        )
    ).fetchone()

    if existing_support:

        # Remove support
        conn.execute(
            """
            DELETE FROM complaint_support

            WHERE complaint_id = ?
            AND student_id = ?
            """,
            (
                complaint_id,
                student_id
            )
        )

        flash(
            "Your support has been removed.",
            "success"
        )

    else:

        # Add support
        conn.execute(
            """
            INSERT INTO complaint_support
            (
                complaint_id,
                student_id
            )
            VALUES (?, ?)
            """,
            (
                complaint_id,
                student_id
            )
        )

        flash(
            "You supported this complaint.",
            "success"
        )

    conn.commit()

    conn.close()

    return redirect(
        url_for(
            "complaint_details",
            complaint_id=complaint_id
        )
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

def get_admin_analytics(conn):

    def grouped_counts(query):
        return [
            {"label": row["label"], "count": row["count"]}
            for row in conn.execute(query).fetchall()
        ]

    total = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    average_support = conn.execute(
        """
        SELECT COALESCE(AVG(support_count), 0)
        FROM (
            SELECT c.id, COUNT(cs.id) AS support_count
            FROM complaints c
            LEFT JOIN complaint_support cs
                ON cs.complaint_id = c.id
            GROUP BY c.id
        )
        """
    ).fetchone()[0]

    resolved_total = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status IN ('Resolved', 'Closed')
        """
    ).fetchone()[0]

    return {
        "total": total,
        "resolved_total": resolved_total,
        "resolution_rate": (
            round((resolved_total / total) * 100, 1)
            if total
            else 0
        ),
        "average_support": round(average_support, 1),
        "status": grouped_counts(
            """
            SELECT status AS label, COUNT(*) AS count
            FROM complaints
            GROUP BY status
            ORDER BY count DESC, label
            """
        ),
        "category": grouped_counts(
            """
            SELECT category AS label, COUNT(*) AS count
            FROM complaints
            GROUP BY category
            ORDER BY count DESC, label
            """
        ),
        "department": grouped_counts(
            """
            SELECT COALESCE(d.name, 'Unassigned') AS label,
                   COUNT(*) AS count
            FROM complaints c
            LEFT JOIN departments d
                ON c.department_id = d.id
            GROUP BY COALESCE(d.name, 'Unassigned')
            ORDER BY count DESC, label
            """
        ),
        "priority": grouped_counts(
            """
            SELECT priority AS label, COUNT(*) AS count
            FROM complaints
            GROUP BY priority
            ORDER BY count DESC, label
            """
        ),
        "monthly": grouped_counts(
            """
            SELECT substr(created_at, 1, 7) AS label, COUNT(*) AS count
            FROM complaints
            GROUP BY substr(created_at, 1, 7)
            ORDER BY label
            """
        )
    }


@app.route("/admin")
def admin_dashboard():

    if session.get("user_type") != "admin":

        return redirect(url_for("login"))

    conn = get_db_connection()

    # All complaints
    complaints = conn.execute(
        """
        SELECT
            c.*,

            s.name AS student_name,
            s.student_id AS student_number,

            d.name AS department_name,

            a.name AS assigned_admin,

            (
                SELECT COUNT(*)
                FROM complaint_support cs
                WHERE cs.complaint_id = c.id
            ) AS support_count

        FROM complaints c

        JOIN students s
            ON c.student_id = s.id

        LEFT JOIN departments d
            ON c.department_id = d.id

        LEFT JOIN admins a
            ON c.assigned_to = a.id

        ORDER BY c.created_at DESC
        """
    ).fetchall()

    # Admin accounts
    admins = conn.execute(
        """
        SELECT id, name, email, role
        FROM admins
        ORDER BY name
        """
    ).fetchall()

    # Statistics
    total = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        """
    ).fetchone()[0]

    new_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'New'
        """
    ).fetchone()[0]

    in_progress = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status = 'In Progress'
        """
    ).fetchone()[0]

    resolved = conn.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status IN ('Resolved', 'Closed')
        """
    ).fetchone()[0]

    pending = total - resolved

    conn.close()

    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        admins=admins,
        total=total,
        new_count=new_count,
        in_progress=in_progress,
        resolved=resolved,
        pending=pending
    )


@app.route("/admin/analytics")
def admin_analytics():

    if session.get("user_type") != "admin":

        return jsonify({"error": "Admin authentication required."}), 401

    conn = get_db_connection()

    try:
        return jsonify(get_admin_analytics(conn))
    finally:
        conn.close()


@app.route("/admin/ai-summary", methods=["POST"])
def admin_ai_summary():

    if session.get("user_type") != "admin":

        return jsonify({"error": "Admin authentication required."}), 401

    conn = get_db_connection()

    try:
        complaints = conn.execute(
            """
            SELECT
                c.title,
                c.description,
                c.category,
                COALESCE(d.name, 'Unassigned') AS department,
                c.priority,
                c.status
            FROM complaints c
            LEFT JOIN departments d
                ON c.department_id = d.id
            ORDER BY c.created_at DESC
            """
        ).fetchall()

        analytics = get_admin_analytics(conn)
    finally:
        conn.close()

    complaint_data = [
        {
            "title": complaint["title"],
            "description": complaint["description"][:600],
            "category": complaint["category"],
            "department": complaint["department"],
            "priority": complaint["priority"],
            "status": complaint["status"]
        }
        for complaint in complaints
    ]

    prompt = f"""
You are helping an authenticated campus administrator review complaint data.
Use only the complaint records and verified aggregate statistics below.
Do not invent counts, causes, or facts. Do not mention or infer student identities.

Return ONLY a concise report of at most 120 words.
Use exactly these headings and one short bullet per heading:
Summary, Category trend, Progress trend, Priority action, Limitation.
Mention only trends supported by the supplied data. Include counts or percentages
from the verified aggregate statistics when useful. Do not repeat complaint text.
Do not add greetings, long explanations, or extra headings.

Verified aggregate statistics:
{analytics}

Complaint records (descriptions may be truncated):
{complaint_data}
"""

    try:
        response = ask_gemini(prompt)
    except Exception:
        return jsonify({
            "error": "The AI service is temporarily unavailable."
        }), 502

    if response.startswith("AI service unavailable") or \
            response.startswith("Gemini API key missing"):
        return jsonify({
            "error": response
        }), 502

    words = response.split()
    if len(words) > 140:
        response = " ".join(words[:140]) + "..."

    return jsonify({"summary": response})


# ============================================================
# ADMIN UPDATE COMPLAINT
# ============================================================

@app.route(
    "/admin/complaint/<int:complaint_id>/update",
    methods=["POST"]
)
def update_complaint(complaint_id):

    if session.get("user_type") != "admin":

        return redirect(url_for("login"))

    new_status = request.form.get(
        "status",
        "New"
    ).strip()

    assigned_to = request.form.get(
        "assigned_to",
        ""
    ).strip()

    resolution = request.form.get(
        "resolution",
        ""
    ).strip()

    allowed_statuses = [
        "New",
        "Verified",
        "Assigned",
        "In Progress",
        "Resolved",
        "Closed"
    ]

    if new_status not in allowed_statuses:

        flash(
            "Invalid complaint status.",
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    conn = get_db_connection()

    # Get old complaint status
    complaint = conn.execute(
        """
        SELECT *
        FROM complaints
        WHERE id = ?
        """,
        (complaint_id,)
    ).fetchone()

    if not complaint:

        conn.close()

        flash(
            "Complaint not found.",
            "error"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    old_status = complaint["status"]

    # Convert empty assignment to NULL
    assigned_admin = (
        int(assigned_to)
        if assigned_to
        else None
    )

    # Resolution timestamp
    if new_status in ["Resolved", "Closed"]:

        conn.execute(
            """
            UPDATE complaints

            SET
                status = ?,
                assigned_to = ?,
                resolution = ?,
                resolved_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
            """,
            (
                new_status,
                assigned_admin,
                resolution,
                complaint_id
            )
        )

    else:

        conn.execute(
            """
            UPDATE complaints

            SET
                status = ?,
                assigned_to = ?,
                resolution = ?,
                resolved_at = NULL,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
            """,
            (
                new_status,
                assigned_admin,
                resolution,
                complaint_id
            )
        )

    # Status history
    if old_status != new_status:

        conn.execute(
            """
            INSERT INTO complaint_status_history
            (
                complaint_id,
                old_status,
                new_status,
                changed_by,
                note
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                complaint_id,
                old_status,
                new_status,
                session["user_id"],
                resolution
            )
        )

        # Notify student
        conn.execute(
            """
            INSERT INTO notifications
            (
                student_id,
                complaint_id,
                message
            )
            VALUES (?, ?, ?)
            """,
            (
                complaint["student_id"],
                complaint_id,
                f"Complaint #{complaint_id} status changed "
                f"from '{old_status}' to '{new_status}'."
            )
        )

    conn.commit()

    conn.close()

    flash(
        f"Complaint #{complaint_id} updated successfully.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# MARK NOTIFICATIONS AS READ
# ============================================================

@app.route("/notifications/read", methods=["POST"])
def mark_notifications_read():

    if session.get("user_type") != "student":

        return redirect(url_for("login"))

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE notifications

        SET is_read = 1

        WHERE student_id = ?
        """,
        (session["user_id"],)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("student_dashboard")
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested page does not exist.</p>
    """, 404


@app.errorhandler(500)
def internal_server_error(error):

    return """
    <h1>500 - Internal Server Error</h1>
    <p>Something went wrong on the server.</p>
    """, 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )