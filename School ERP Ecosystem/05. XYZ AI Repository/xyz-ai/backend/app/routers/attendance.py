"""
/attendance/* endpoints — thin HTTP glue only.

Every real decision (who can see what, who can mark what) happens in
app/mock_api/attendance.py. This file's only job is: extract the
verified CurrentUser, call the business logic, translate exceptions to
HTTP status codes. If you find yourself adding an `if current_user.role
== ...` check directly in this file, that logic belongs in mock_api/
instead — keep it in one place.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user, require_role, CurrentUser
from app.models.schemas import AttendanceRecord, AttendanceStatus, Role
from app.mock_api import attendance as attendance_service
from app.mock_api.attendance import NotFoundError, ForbiddenError, BadRequestError

router = APIRouter(prefix="/attendance", tags=["attendance"])


class MarkEntry(BaseModel):
    student_id: str
    status: AttendanceStatus


class MarkAttendanceRequest(BaseModel):
    class_id: str
    entries: list[MarkEntry]
    date: Optional[date] = None  # defaults to today if omitted


def _raise_for(exc: Exception):
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ForbiddenError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, BadRequestError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc  # unexpected — let it surface as a 500, don't silently swallow


# IMPORTANT: fixed/literal paths (/mark, /summary/school) MUST be
# registered before the dynamic /{student_id} route. FastAPI matches
# routes in registration order, and {student_id} would otherwise
# greedily match "mark" or "summary" as if they were a student id.

@router.post("/mark", response_model=list[AttendanceRecord])
def mark_attendance(
    payload: MarkAttendanceRequest,
    current_user: CurrentUser = Depends(require_role(Role.TEACHER)),
):
    entries = [(e.student_id, e.status) for e in payload.entries]
    try:
        return attendance_service.mark_class_attendance(
            current_user, payload.class_id, entries, on_date=payload.date
        )
    except (NotFoundError, ForbiddenError, BadRequestError) as exc:
        _raise_for(exc)


@router.get("/summary/school")
def school_summary(current_user: CurrentUser = Depends(require_role(Role.PRINCIPAL))):
    try:
        return attendance_service.get_school_attendance_summary(current_user)
    except ForbiddenError as exc:
        _raise_for(exc)


@router.get("/{student_id}", response_model=list[AttendanceRecord])
def view_attendance(student_id: str, current_user: CurrentUser = Depends(get_current_user)):
    try:
        return attendance_service.get_student_attendance(current_user, student_id)
    except (NotFoundError, ForbiddenError) as exc:
        _raise_for(exc)