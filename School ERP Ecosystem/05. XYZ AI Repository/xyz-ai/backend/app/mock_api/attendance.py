"""
Attendance mock API — business logic + authorization.

Every function here re-checks permissions from scratch using ONLY the
verified CurrentUser (role + profile_id from the JWT) and the seed data
relationships. Nothing here trusts a role or id passed in a request body —
that's exactly the "fake role claims" attack the assessment warns about.

This file has zero FastAPI imports. It raises plain Python exceptions;
the router layer (routers/attendance.py) is responsible for translating
those into HTTP status codes. This separation means these authorization
rules can be unit tested directly, with no HTTP server involved.
"""

from datetime import date
from typing import Optional
from uuid import uuid4

from app.auth.dependencies import CurrentUser
from app.models.schemas import AttendanceRecord, AttendanceStatus, Role
from app.models.seed_data import STUDENTS, PARENTS, TEACHERS, CLASSES, ATTENDANCE


class NotFoundError(Exception):
    pass


class ForbiddenError(Exception):
    pass


class BadRequestError(Exception):
    pass


def _can_view_student(current_user: CurrentUser, student_id: str) -> bool:
    """Single source of truth for 'who is allowed to see this student's data'."""
    if current_user.role == Role.PRINCIPAL:
        return True

    if current_user.role == Role.STUDENT:
        return current_user.profile_id == student_id

    if current_user.role == Role.PARENT:
        parent = PARENTS.get(current_user.profile_id)
        return parent is not None and student_id in parent.child_ids

    if current_user.role == Role.TEACHER:
        teacher = TEACHERS.get(current_user.profile_id)
        if teacher is None:
            return False
        student = STUDENTS.get(student_id)
        return student is not None and student.class_id in teacher.class_ids

    return False


def get_student_attendance(current_user: CurrentUser, student_id: str) -> list[AttendanceRecord]:
    if student_id not in STUDENTS:
        raise NotFoundError(f"No student with id {student_id}")

    if not _can_view_student(current_user, student_id):
        raise ForbiddenError("You are not permitted to view this student's attendance")

    records = [r for r in ATTENDANCE if r.student_id == student_id]
    return sorted(records, key=lambda r: r.date)


def mark_class_attendance(
    current_user: CurrentUser,
    class_id: str,
    entries: list[tuple[str, AttendanceStatus]],
    on_date: Optional[date] = None,
) -> list[AttendanceRecord]:
    """
    entries: list of (student_id, status) pairs.
    Re-marking the same student on the same date UPDATES the existing
    record rather than creating a duplicate — a teacher correcting a
    mistake shouldn't leave two conflicting rows for the same day.
    """
    if current_user.role != Role.TEACHER:
        raise ForbiddenError("Only teachers can mark attendance")

    classroom = CLASSES.get(class_id)
    if classroom is None:
        raise NotFoundError(f"No class with id {class_id}")

    teacher = TEACHERS.get(current_user.profile_id)
    if teacher is None or class_id not in teacher.class_ids:
        raise ForbiddenError("You do not teach this class")

    mark_date = on_date or date.today()
    results: list[AttendanceRecord] = []

    for student_id, status in entries:
        if student_id not in classroom.student_ids:
            raise BadRequestError(f"Student {student_id} is not in class {class_id}")

        existing = next(
            (r for r in ATTENDANCE if r.student_id == student_id and r.date == mark_date),
            None,
        )
        if existing is not None:
            existing.status = status
            existing.marked_by = current_user.profile_id
            results.append(existing)
        else:
            record = AttendanceRecord(
                id=str(uuid4()),
                student_id=student_id,
                date=mark_date,
                status=status,
                marked_by=current_user.profile_id,
            )
            ATTENDANCE.append(record)
            results.append(record)

    return results


def get_school_attendance_summary(current_user: CurrentUser) -> dict:
    """Principal-only: overall school attendance analytics."""
    if current_user.role != Role.PRINCIPAL:
        raise ForbiddenError("Only the principal can view school-wide attendance analytics")

    total = len(ATTENDANCE)
    present = len([r for r in ATTENDANCE if r.status == AttendanceStatus.PRESENT])
    absent = len([r for r in ATTENDANCE if r.status == AttendanceStatus.ABSENT])
    late = len([r for r in ATTENDANCE if r.status == AttendanceStatus.LATE])

    per_class: dict[str, dict] = {}
    for cid, classroom in CLASSES.items():
        class_records = [r for r in ATTENDANCE if r.student_id in classroom.student_ids]
        class_present = len([r for r in class_records if r.status == AttendanceStatus.PRESENT])
        per_class[cid] = {
            "class_name": classroom.name,
            "total_records": len(class_records),
            "present": class_present,
            "attendance_rate": round(class_present / len(class_records) * 100, 1) if class_records else None,
        }

    return {
        "total_records": total,
        "present": present,
        "absent": absent,
        "late": late,
        "overall_attendance_rate": round(present / total * 100, 1) if total else None,
        "by_class": per_class,
    }