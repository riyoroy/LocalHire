"""
SQLite Database Layer for Local Hire.
Enforces foreign keys, unique constraints, and backend rules for blacklist & strike suspensions.
"""

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

DB_FILENAME = "localhire.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, DB_FILENAME)


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates a sqlite3 connection with Row factory and foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _hash_seed_password(password: str) -> Tuple[str, str]:
    """Generates salt and sha256 hash for seed accounts."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return pwd_hash, salt


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes tables and seeds initial data if database is fresh."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT CHECK(role IN ('worker', 'employer', 'admin')) NOT NULL,
        district TEXT NOT NULL,
        locality TEXT NOT NULL,
        is_blacklisted INTEGER DEFAULT 0,  -- For employers
        is_suspended INTEGER DEFAULT 0,    -- For workers
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Jobs table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        job_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employer_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        district TEXT NOT NULL,
        locality TEXT NOT NULL,
        job_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        payment REAL NOT NULL,
        status TEXT DEFAULT 'open' CHECK(status IN ('open', 'filled', 'completed', 'cancelled')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employer_id) REFERENCES users(user_id)
    );
    """)

    # 3. Applications table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        application_id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        worker_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected', 'completed')),
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(job_id, worker_id),
        FOREIGN KEY (job_id) REFERENCES jobs(job_id),
        FOREIGN KEY (worker_id) REFERENCES users(user_id)
    );
    """)

    # 4. Complaints table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_type TEXT CHECK(complaint_type IN ('non_payment', 'no_show')) NOT NULL,
        job_id INTEGER NOT NULL,
        complainant_id INTEGER NOT NULL,
        accused_id INTEGER NOT NULL,
        details TEXT NOT NULL,
        agreed_payment REAL,
        status TEXT DEFAULT 'submitted' CHECK(status IN ('submitted', 'under_review', 'verified', 'dismissed')),
        admin_notes TEXT,
        reviewed_by INTEGER,
        reviewed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs(job_id),
        FOREIGN KEY (complainant_id) REFERENCES users(user_id),
        FOREIGN KEY (accused_id) REFERENCES users(user_id),
        FOREIGN KEY (reviewed_by) REFERENCES users(user_id)
    );
    """)

    # 5. Strikes table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS strikes (
        strike_id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id INTEGER NOT NULL,
        complaint_id INTEGER NOT NULL,
        reason TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (worker_id) REFERENCES users(user_id),
        FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
    );
    """)

    conn.commit()

    # Seed data if jobs count is 0
    cur.execute("SELECT COUNT(*) as count FROM jobs")
    job_count = cur.fetchone()["count"]

    if job_count == 0:
        # Seed Admin user
        admin_hash, admin_salt = _hash_seed_password("admin123")
        cur.execute("""
        INSERT OR IGNORE INTO users (name, phone, password_hash, salt, role, district, locality)
        VALUES (?, ?, ?, ?, 'admin', 'Ernakulam', 'Kaloor, Ernakulam')
        """, ("System Administrator", "0000000000", admin_hash, admin_salt))

        # Seed Employer user
        emp_hash, emp_salt = _hash_seed_password("pass123")
        cur.execute("""
        INSERT OR IGNORE INTO users (name, phone, password_hash, salt, role, district, locality)
        VALUES (?, ?, ?, ?, 'employer', 'Kollam', 'Chinnakada, Kollam')
        """, ("Anand Retailers", "9876543210", emp_hash, emp_salt))

        # Seed Worker user
        wkr_hash, wkr_salt = _hash_seed_password("pass123")
        cur.execute("""
        INSERT OR IGNORE INTO users (name, phone, password_hash, salt, role, district, locality)
        VALUES (?, ?, ?, ?, 'worker', 'Kollam', 'Kundara, Kollam')
        """, ("Rahul K", "9123456789", wkr_hash, wkr_salt))

        conn.commit()

        # Retrieve employer id
        cur.execute("SELECT user_id FROM users WHERE phone = '9876543210'")
        emp_row = cur.fetchone()
        if emp_row:
            employer_id = emp_row["user_id"]

            sample_jobs = [
                (
                    employer_id,
                    "Sales Assistant",
                    "Retail",
                    "Kollam",
                    "Chinnakada, Kollam",
                    "2026-11-15",
                    "09:00",
                    "18:00",
                    600.0,
                    "open",
                ),
                (
                    employer_id,
                    "Wedding Catering Server",
                    "Hospitality",
                    "Ernakulam",
                    "Kaloor, Ernakulam",
                    "2026-11-16",
                    "17:00",
                    "23:00",
                    500.0,
                    "open",
                ),
                (
                    employer_id,
                    "Inventory Helper",
                    "Logistics",
                    "Thiruvananthapuram",
                    "Palayam, Thiruvananthapuram",
                    "2026-11-17",
                    "08:00",
                    "14:00",
                    400.0,
                    "open",
                ),
                (
                    employer_id,
                    "Customer Calling Assistant",
                    "Telemarketing",
                    "Ernakulam",
                    "Edappally, Ernakulam",
                    "2026-11-18",
                    "10:00",
                    "15:00",
                    350.0,
                    "open",
                ),
            ]

            cur.executemany("""
            INSERT INTO jobs (employer_id, title, category, district, locality, job_date, start_time, end_time, payment, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_jobs)
            conn.commit()

    conn.close()


# ==============================================================================
# USER OPERATIONS
# ==============================================================================

def get_user_by_phone(phone: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetches user record by phone number."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE phone = ?", (phone.strip(),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetches user record by user_id."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(
    name: str,
    phone: str,
    password_hash: str,
    salt: str,
    role: str,
    district: str,
    locality: str,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Registers a new user. Raises ValueError on duplicate phone or validation error."""
    phone = phone.strip()
    if not (phone.isdigit() and len(phone) == 10):
        raise ValueError("Phone number must be exactly 10 digits.")

    if role not in ("worker", "employer", "admin"):
        raise ValueError("Invalid user role specified.")

    conn = get_connection(db_path)
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO users (name, phone, password_hash, salt, role, district, locality)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name.strip(), phone, password_hash, salt, role, district.strip(), locality.strip()))
        conn.commit()
        user_id = cur.lastrowid
        return user_id
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: users.phone" in str(e):
            raise ValueError(f"Phone number '{phone}' is already registered.")
        raise ValueError(f"Registration error: {e}")
    finally:
        conn.close()


def get_all_users(role: Optional[str] = None, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all users, optionally filtered by role."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    if role:
        cur.execute("SELECT * FROM users WHERE role = ? ORDER BY user_id DESC", (role,))
    else:
        cur.execute("SELECT * FROM users ORDER BY user_id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==============================================================================
# JOB OPERATIONS
# ==============================================================================

def create_job(
    employer_id: int,
    title: str,
    category: str,
    district: str,
    locality: str,
    job_date: str,
    start_time: str,
    end_time: str,
    payment: float,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """
    Creates a new job posting.
    STRICT BACKEND ENFORCEMENT: Rejects job creation if employer is blacklisted.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    # Verify employer account and blacklist status
    cur.execute("SELECT role, is_blacklisted FROM users WHERE user_id = ?", (employer_id,))
    emp = cur.fetchone()
    if not emp:
        conn.close()
        raise ValueError("Employer account not found.")

    if emp["role"] != "employer":
        conn.close()
        raise ValueError("Only registered employers can post jobs.")

    if emp["is_blacklisted"] == 1:
        conn.close()
        raise ValueError(
            "Account is blacklisted due to verified wage theft or non-payment disputes. Job posting is forbidden."
        )

    if payment <= 0:
        conn.close()
        raise ValueError("Payment amount must be greater than zero.")

    cur.execute("""
    INSERT INTO jobs (employer_id, title, category, district, locality, job_date, start_time, end_time, payment, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
    """, (
        employer_id,
        title.strip(),
        category.strip(),
        district.strip(),
        locality.strip(),
        job_date.strip(),
        start_time.strip(),
        end_time.strip(),
        float(payment),
    ))
    conn.commit()
    job_id = cur.lastrowid
    conn.close()
    return job_id


def get_jobs(
    status: Optional[str] = "open",
    category: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """Fetches jobs joined with employer profile details."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    query = """
    SELECT j.*, u.name as employer_name, u.phone as employer_phone, u.locality as employer_locality
    FROM jobs j
    JOIN users u ON j.employer_id = u.user_id
    WHERE 1=1
    """
    params: List[Any] = []

    if status and status != "all":
        query += " AND j.status = ?"
        params.append(status)

    if category and category != "All Categories":
        query += " AND j.category = ?"
        params.append(category)

    query += " ORDER BY j.job_id DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_jobs_by_employer(employer_id: int, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all jobs posted by a specific employer with applicant counts."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT j.*,
           COUNT(a.application_id) as applicant_count,
           SUM(CASE WHEN a.status = 'pending' THEN 1 ELSE 0 END) as pending_applicant_count,
           SUM(CASE WHEN a.status = 'accepted' THEN 1 ELSE 0 END) as accepted_applicant_count
    FROM jobs j
    LEFT JOIN applications a ON j.job_id = a.job_id
    WHERE j.employer_id = ?
    GROUP BY j.job_id
    ORDER BY j.job_id DESC
    """, (employer_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_job_by_id(job_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetches a specific job by ID with employer info."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT j.*, u.name as employer_name, u.phone as employer_phone, u.locality as employer_locality
    FROM jobs j
    JOIN users u ON j.employer_id = u.user_id
    WHERE j.job_id = ?
    """, (job_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_job_status(job_id: int, new_status: str, employer_id: Optional[int] = None, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Updates job status (open, filled, completed, cancelled)."""
    if new_status not in ("open", "filled", "completed", "cancelled"):
        raise ValueError("Invalid job status.")

    conn = get_connection(db_path)
    cur = conn.cursor()

    if employer_id is not None:
        cur.execute("SELECT employer_id FROM jobs WHERE job_id = ?", (job_id,))
        job = cur.fetchone()
        if not job or job["employer_id"] != employer_id:
            conn.close()
            raise ValueError("Unauthorized to update this job.")

    cur.execute("UPDATE jobs SET status = ? WHERE job_id = ?", (new_status, job_id))
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated


# ==============================================================================
# APPLICATION OPERATIONS
# ==============================================================================

def apply_for_job(job_id: int, worker_id: int, db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Worker applies for a job.
    STRICT BACKEND ENFORCEMENT: Rejects application if worker is suspended.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    # Verify worker role and suspension status
    cur.execute("SELECT role, is_suspended FROM users WHERE user_id = ?", (worker_id,))
    worker = cur.fetchone()
    if not worker:
        conn.close()
        raise ValueError("Worker account not found.")

    if worker["role"] != "worker":
        conn.close()
        raise ValueError("Only registered workers can apply for jobs.")

    if worker["is_suspended"] == 1:
        conn.close()
        raise ValueError(
            "Account is suspended due to active strikes. You cannot apply for jobs."
        )

    # Check job status
    cur.execute("SELECT status FROM jobs WHERE job_id = ?", (job_id,))
    job = cur.fetchone()
    if not job:
        conn.close()
        raise ValueError("Job not found.")

    if job["status"] != "open":
        conn.close()
        raise ValueError("This job is no longer accepting applications.")

    # Check existing application
    cur.execute("SELECT application_id, status FROM applications WHERE job_id = ? AND worker_id = ?", (job_id, worker_id))
    existing = cur.fetchone()
    if existing:
        conn.close()
        raise ValueError(f"You have already applied for this job (Status: {existing['status']}).")

    try:
        cur.execute("""
        INSERT INTO applications (job_id, worker_id, status)
        VALUES (?, ?, 'pending')
        """, (job_id, worker_id))
        conn.commit()
        app_id = cur.lastrowid
        conn.close()
        return app_id
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"Application error: {e}")


def get_worker_applications(worker_id: int, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all applications submitted by a worker with job and employer details."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT a.*,
           j.title as job_title, j.category as job_category, j.district as job_district,
           j.locality as job_locality, j.job_date, j.start_time, j.end_time, j.payment,
           j.status as job_status, j.employer_id,
           u.name as employer_name, u.phone as employer_phone
    FROM applications a
    JOIN jobs j ON a.job_id = j.job_id
    JOIN users u ON j.employer_id = u.user_id
    WHERE a.worker_id = ?
    ORDER BY a.application_id DESC
    """, (worker_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_job_applicants(job_id: int, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all applicants for a given job with worker profile & active strikes."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT a.*,
           u.name as worker_name, u.phone as worker_phone, u.district as worker_district,
           u.locality as worker_locality, u.is_suspended as worker_is_suspended,
           (SELECT COUNT(*) FROM strikes s WHERE s.worker_id = u.user_id AND s.is_active = 1) as active_strikes_count
    FROM applications a
    JOIN users u ON a.worker_id = u.user_id
    WHERE a.job_id = ?
    ORDER BY a.application_id DESC
    """, (job_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_application_status(
    application_id: int,
    new_status: str,
    employer_id: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> bool:
    """Updates applicant status ('accepted', 'rejected', 'completed')."""
    if new_status not in ("pending", "accepted", "rejected", "completed"):
        raise ValueError("Invalid application status.")

    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
    SELECT a.job_id, j.employer_id
    FROM applications a
    JOIN jobs j ON a.job_id = j.job_id
    WHERE a.application_id = ?
    """, (application_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Application not found.")

    if employer_id is not None and row["employer_id"] != employer_id:
        conn.close()
        raise ValueError("Unauthorized to update this application.")

    cur.execute("UPDATE applications SET status = ? WHERE application_id = ?", (new_status, application_id))
    conn.commit()
    conn.close()
    return True


# ==============================================================================
# COMPLAINTS & DISPUTE OPERATIONS
# ==============================================================================

def file_complaint(
    complaint_type: str,
    job_id: int,
    complainant_id: int,
    accused_id: int,
    details: str,
    agreed_payment: Optional[float] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """
    Submits a dispute complaint.
    Strictly verifies roles and application prerequisites:
    - 'non_payment': Complainant must be a worker whose application was accepted or completed.
    - 'no_show': Complainant must be an employer who accepted this worker.
    """
    if complaint_type not in ("non_payment", "no_show"):
        raise ValueError("Complaint type must be 'non_payment' or 'no_show'.")

    if not details.strip():
        raise ValueError("Complaint details cannot be blank.")

    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Non-Payment dispute verification
    if complaint_type == "non_payment":
        cur.execute("SELECT role FROM users WHERE user_id = ?", (complainant_id,))
        comp = cur.fetchone()
        if not comp or comp["role"] != "worker":
            conn.close()
            raise ValueError("Only workers can lodge non-payment complaints.")

        # Worker must have an accepted or completed application for this job
        cur.execute("""
        SELECT a.status, j.payment, j.employer_id
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        WHERE a.job_id = ? AND a.worker_id = ?
        """, (job_id, complainant_id))
        app_row = cur.fetchone()
        if not app_row:
            conn.close()
            raise ValueError("No record found of you working on this job.")

        if app_row["status"] not in ("accepted", "completed"):
            conn.close()
            raise ValueError("Non-payment disputes can only be lodged for jobs marked 'accepted' or 'completed'.")

        accused_id = app_row["employer_id"]
        if agreed_payment is None or agreed_payment <= 0:
            agreed_payment = app_row["payment"]

    # 2. No-Show dispute verification
    elif complaint_type == "no_show":
        cur.execute("SELECT role FROM users WHERE user_id = ?", (complainant_id,))
        comp = cur.fetchone()
        if not comp or comp["role"] != "employer":
            conn.close()
            raise ValueError("Only employers can report worker no-shows.")

        cur.execute("""
        SELECT a.status, j.employer_id, j.payment
        FROM applications a
        JOIN jobs j ON a.job_id = j.job_id
        WHERE a.job_id = ? AND a.worker_id = ?
        """, (job_id, accused_id))
        app_row = cur.fetchone()
        if not app_row or app_row["employer_id"] != complainant_id:
            conn.close()
            raise ValueError("This job does not belong to you or worker did not apply.")

        if app_row["status"] != "accepted":
            conn.close()
            raise ValueError("No-show disputes can only be filed against accepted workers.")

        if agreed_payment is None:
            agreed_payment = app_row["payment"]

    cur.execute("""
    INSERT INTO complaints (complaint_type, job_id, complainant_id, accused_id, details, agreed_payment, status)
    VALUES (?, ?, ?, ?, ?, ?, 'submitted')
    """, (complaint_type, job_id, complainant_id, accused_id, details.strip(), agreed_payment))
    conn.commit()
    complaint_id = cur.lastrowid
    conn.close()
    return complaint_id


def get_all_complaints(
    complaint_type: Optional[str] = None,
    status: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """Fetches all complaints with complainant, accused, and job details."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    query = """
    SELECT c.*,
           j.title as job_title, j.category as job_category, j.district as job_district,
           j.locality as job_locality, j.job_date, j.payment as job_payment,
           u1.name as complainant_name, u1.phone as complainant_phone, u1.role as complainant_role,
           u2.name as accused_name, u2.phone as accused_phone, u2.role as accused_role,
           u2.is_blacklisted as accused_is_blacklisted, u2.is_suspended as accused_is_suspended
    FROM complaints c
    JOIN jobs j ON c.job_id = j.job_id
    JOIN users u1 ON c.complainant_id = u1.user_id
    JOIN users u2 ON c.accused_id = u2.user_id
    WHERE 1=1
    """
    params: List[Any] = []

    if complaint_type and complaint_type != "all":
        query += " AND c.complaint_type = ?"
        params.append(complaint_type)

    if status and status != "all":
        query += " AND c.status = ?"
        params.append(status)

    query += " ORDER BY c.complaint_id DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_complaints_by_user(user_id: int, as_complainant: bool = True, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches complaints lodged by or against a user."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    col = "c.complainant_id" if as_complainant else "c.accused_id"
    cur.execute(f"""
    SELECT c.*, j.title as job_title, u.name as other_party_name, u.phone as other_party_phone
    FROM complaints c
    JOIN jobs j ON c.job_id = j.job_id
    JOIN users u ON {'c.accused_id' if as_complainant else 'c.complainant_id'} = u.user_id
    WHERE {col} = ?
    ORDER BY c.complaint_id DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def review_complaint(
    complaint_id: int,
    new_status: str,
    admin_id: int,
    admin_notes: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """
    Admin resolves a complaint.
    STRICT BACKEND ENFORCEMENT:
    - If non_payment verified: Accused employer is blacklisted (is_blacklisted = 1).
    - If no_show verified: Issue a strike to accused worker. If active strikes >= 3, suspend worker (is_suspended = 1).
    """
    if new_status not in ("verified", "dismissed", "under_review"):
        raise ValueError("Invalid review status.")

    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,))
    complaint = cur.fetchone()
    if not complaint:
        conn.close()
        raise ValueError("Complaint not found.")

    c_dict = dict(complaint)
    accused_id = c_dict["accused_id"]
    complaint_type = c_dict["complaint_type"]

    # Update complaint
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
    UPDATE complaints
    SET status = ?, admin_notes = ?, reviewed_by = ?, reviewed_at = ?
    WHERE complaint_id = ?
    """, (new_status, admin_notes.strip(), admin_id, now, complaint_id))

    result_info = {
        "status": new_status,
        "complaint_type": complaint_type,
        "employer_blacklisted": False,
        "strike_issued": False,
        "worker_suspended": False,
        "active_strikes": 0,
    }

    if new_status == "verified":
        if complaint_type == "non_payment":
            # Blacklist employer
            cur.execute("UPDATE users SET is_blacklisted = 1 WHERE user_id = ?", (accused_id,))
            result_info["employer_blacklisted"] = True

        elif complaint_type == "no_show":
            # Issue strike for worker
            cur.execute("""
            INSERT INTO strikes (worker_id, complaint_id, reason, is_active)
            VALUES (?, ?, ?, 1)
            """, (accused_id, complaint_id, f"Verified No-Show complaint #{complaint_id}"))
            result_info["strike_issued"] = True

            # Calculate active strikes
            cur.execute("SELECT COUNT(*) as strike_count FROM strikes WHERE worker_id = ? AND is_active = 1", (accused_id,))
            strike_count = cur.fetchone()["strike_count"]
            result_info["active_strikes"] = strike_count

            # If >= 3 strikes, suspend worker
            if strike_count >= 3:
                cur.execute("UPDATE users SET is_suspended = 1 WHERE user_id = ?", (accused_id,))
                result_info["worker_suspended"] = True

    conn.commit()
    conn.close()
    return result_info


# ==============================================================================
# STRIKES OPERATIONS
# ==============================================================================

def get_all_strikes(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all strike records with worker and complaint details."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT s.*,
           u.name as worker_name, u.phone as worker_phone, u.is_suspended as worker_is_suspended,
           c.job_id, c.details as complaint_details, j.title as job_title
    FROM strikes s
    JOIN users u ON s.worker_id = u.user_id
    JOIN complaints c ON s.complaint_id = c.complaint_id
    JOIN jobs j ON c.job_id = j.job_id
    ORDER BY s.strike_id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_worker_strikes(worker_id: int, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all strikes for a given worker."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT s.*, c.job_id, j.title as job_title
    FROM strikes s
    JOIN complaints c ON s.complaint_id = c.complaint_id
    JOIN jobs j ON c.job_id = j.job_id
    WHERE s.worker_id = ?
    ORDER BY s.strike_id DESC
    """, (worker_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def reverse_strike(strike_id: int, admin_id: Optional[int] = None, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """
    Reverses an active strike.
    STRICT BACKEND ENFORCEMENT:
    If worker's active strike count drops below 3, suspension is automatically lifted (is_suspended = 0).
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT * FROM strikes WHERE strike_id = ?", (strike_id,))
    strike = cur.fetchone()
    if not strike:
        conn.close()
        raise ValueError("Strike record not found.")

    worker_id = strike["worker_id"]

    # Mark strike as inactive
    cur.execute("UPDATE strikes SET is_active = 0 WHERE strike_id = ?", (strike_id,))

    # Recalculate remaining active strikes for worker
    cur.execute("SELECT COUNT(*) as active_count FROM strikes WHERE worker_id = ? AND is_active = 1", (worker_id,))
    remaining_strikes = cur.fetchone()["active_count"]

    suspension_cleared = False
    if remaining_strikes < 3:
        cur.execute("UPDATE users SET is_suspended = 0 WHERE user_id = ?", (worker_id,))
        suspension_cleared = True

    conn.commit()
    conn.close()

    return {
        "strike_id": strike_id,
        "worker_id": worker_id,
        "remaining_active_strikes": remaining_strikes,
        "suspension_cleared": suspension_cleared,
    }


# ==============================================================================
# ADMIN METRICS
# ==============================================================================

def get_admin_metrics(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Calculates comprehensive system statistics for the Admin Console."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as c FROM users WHERE role = 'worker'")
    total_workers = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM users WHERE role = 'employer'")
    total_employers = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM jobs")
    total_jobs = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM jobs WHERE status = 'open'")
    open_jobs = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM applications")
    total_applications = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM complaints WHERE status = 'submitted'")
    pending_complaints = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM complaints WHERE complaint_type = 'non_payment' AND status = 'submitted'")
    pending_wage_disputes = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM complaints WHERE complaint_type = 'no_show' AND status = 'submitted'")
    pending_no_show_disputes = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM users WHERE is_blacklisted = 1")
    blacklisted_employers = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM users WHERE is_suspended = 1")
    suspended_workers = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) as c FROM strikes WHERE is_active = 1")
    active_strikes = cur.fetchone()["c"]

    conn.close()

    return {
        "total_workers": total_workers,
        "total_employers": total_employers,
        "total_jobs": total_jobs,
        "open_jobs": open_jobs,
        "total_applications": total_applications,
        "pending_complaints": pending_complaints,
        "pending_wage_disputes": pending_wage_disputes,
        "pending_no_show_disputes": pending_no_show_disputes,
        "blacklisted_employers": blacklisted_employers,
        "suspended_workers": suspended_workers,
        "active_strikes": active_strikes,
    }

