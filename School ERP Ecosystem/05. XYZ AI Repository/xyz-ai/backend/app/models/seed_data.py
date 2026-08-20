"""
Mock in-memory "database" for XYZ AI.

Why validation-at-import: this data is hand-written, and hand-written
relational data breaks silently (e.g. you rename a student's id in one
place but forget the parent's child_ids list). If that happens, you do NOT
want to discover it when a demo query returns an empty attendance record —
you want the app to refuse to start, with a clear error pointing at the
broken reference.

Test login credentials (plaintext, for local dev only — never do this
with real passwords in a real system):
    student_rahul  / password123
    parent_sunita  / password123
    teacher_verma  / password123
    principal_rao  / password123
"""

from datetime import date, timedelta
from passlib.hash import bcrypt

from app.models.schemas import (
    Student, Parent, Teacher, Principal, ClassRoom,
    UserAccount, Role, AttendanceRecord, AttendanceStatus,
)

# ---------------------------------------------------------------------------
# Role profiles
# ---------------------------------------------------------------------------

CLASSES = {
    "class_10a": ClassRoom(
        id="class_10a", name="10-A",
        teacher_id="teacher_verma",
        student_ids=["student_rahul", "student_priya"],
    ),
}

TEACHERS = {
    "teacher_verma": Teacher(id="teacher_verma", name="Mrs. Verma", class_ids=["class_10a"]),
}

PRINCIPALS = {
    "principal_rao": Principal(id="principal_rao", name="Dr. Rao"),
}

STUDENTS = {
    "student_rahul": Student(
        id="student_rahul", name="Rahul Sharma",
        class_id="class_10a", parent_ids=["parent_sunita"],
    ),
    "student_priya": Student(
        id="student_priya", name="Priya Sharma",  # sibling of Rahul — same parent
        class_id="class_10a", parent_ids=["parent_sunita"],
    ),
}

PARENTS = {
    "parent_sunita": Parent(
        id="parent_sunita", name="Sunita Sharma",
        child_ids=["student_rahul", "student_priya"],
    ),
}

# ---------------------------------------------------------------------------
# Auth accounts (role + profile_id linkage)
# ---------------------------------------------------------------------------

_TEST_PASSWORD_HASH = bcrypt.hash("password123")

USER_ACCOUNTS = {
    "student_rahul_acct": UserAccount(
        id="student_rahul_acct", username="student_rahul",
        password_hash=_TEST_PASSWORD_HASH, role=Role.STUDENT,
        profile_id="student_rahul",
    ),
    "parent_sunita_acct": UserAccount(
        id="parent_sunita_acct", username="parent_sunita",
        password_hash=_TEST_PASSWORD_HASH, role=Role.PARENT,
        profile_id="parent_sunita",
    ),
    "teacher_verma_acct": UserAccount(
        id="teacher_verma_acct", username="teacher_verma",
        password_hash=_TEST_PASSWORD_HASH, role=Role.TEACHER,
        profile_id="teacher_verma",
    ),
    "principal_rao_acct": UserAccount(
        id="principal_rao_acct", username="principal_rao",
        password_hash=_TEST_PASSWORD_HASH, role=Role.PRINCIPAL,
        profile_id="principal_rao",
    ),
}

# ---------------------------------------------------------------------------
# Attendance records (last 3 days, for demo purposes)
# ---------------------------------------------------------------------------

_today = date.today()

ATTENDANCE: list[AttendanceRecord] = [
    AttendanceRecord(id="att_1", student_id="student_rahul", date=_today - timedelta(days=2),
                      status=AttendanceStatus.PRESENT, marked_by="teacher_verma"),
    AttendanceRecord(id="att_2", student_id="student_rahul", date=_today - timedelta(days=1),
                      status=AttendanceStatus.ABSENT, marked_by="teacher_verma"),
    AttendanceRecord(id="att_3", student_id="student_rahul", date=_today,
                      status=AttendanceStatus.PRESENT, marked_by="teacher_verma"),
    AttendanceRecord(id="att_4", student_id="student_priya", date=_today,
                      status=AttendanceStatus.PRESENT, marked_by="teacher_verma"),
]


# ---------------------------------------------------------------------------
# Referential integrity validation — runs once at import time.
# ---------------------------------------------------------------------------

def _validate_referential_integrity() -> None:
    errors: list[str] = []

    for sid, student in STUDENTS.items():
        if student.class_id not in CLASSES:
            errors.append(f"Student {sid} references missing class_id {student.class_id}")
        for pid in student.parent_ids:
            if pid not in PARENTS:
                errors.append(f"Student {sid} references missing parent_id {pid}")
            elif sid not in PARENTS[pid].child_ids:
                errors.append(f"Student {sid} lists parent {pid}, but {pid}.child_ids does not list {sid} back")

    for pid, parent in PARENTS.items():
        for sid in parent.child_ids:
            if sid not in STUDENTS:
                errors.append(f"Parent {pid} references missing child_id {sid}")

    for tid, teacher in TEACHERS.items():
        for cid in teacher.class_ids:
            if cid not in CLASSES:
                errors.append(f"Teacher {tid} references missing class_id {cid}")
            elif CLASSES[cid].teacher_id != tid:
                errors.append(f"Teacher {tid} claims class {cid}, but {cid}.teacher_id is {CLASSES[cid].teacher_id}")

    for cid, classroom in CLASSES.items():
        for sid in classroom.student_ids:
            if sid not in STUDENTS:
                errors.append(f"Class {cid} references missing student_id {sid}")
            elif STUDENTS[sid].class_id != cid:
                errors.append(f"Class {cid} lists student {sid}, but {sid}.class_id is {STUDENTS[sid].class_id}")

    for acct_id, acct in USER_ACCOUNTS.items():
        role_table = {
            Role.STUDENT: STUDENTS, Role.PARENT: PARENTS,
            Role.TEACHER: TEACHERS, Role.PRINCIPAL: PRINCIPALS,
        }[acct.role]
        if acct.profile_id not in role_table:
            errors.append(f"UserAccount {acct_id} (role={acct.role}) references missing profile_id {acct.profile_id}")

    for record in ATTENDANCE:
        if record.student_id not in STUDENTS:
            errors.append(f"AttendanceRecord {record.id} references missing student_id {record.student_id}")
        if record.marked_by not in TEACHERS:
            errors.append(f"AttendanceRecord {record.id} references missing teacher_id {record.marked_by}")

    if errors:
        raise AssertionError(
            "Seed data referential integrity check FAILED — fix seed_data.py before starting the app:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )


_validate_referential_integrity()
