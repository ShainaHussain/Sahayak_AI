"""
Tool factory for the chat agent.

KEY DESIGN RULE: build_tools_for_user() is called ONCE PER REQUEST with
the verified CurrentUser from the JWT. The tools it returns are closures
over that specific user — there is no way for the LLM to pass in a
different user_id or role and have a tool act on someone else's behalf,
because the tools never accept user identity as an argument at all.

A second rule: only tools relevant to the user's role are handed to the
LLM in the first place. This isn't the real security boundary — mock_api's
internal checks are — but it narrows what a prompt injection could try.
"""

from langchain_core.tools import tool

from app.auth.dependencies import CurrentUser
from app.models.schemas import AttendanceStatus, Role
from app.models.seed_data import STUDENTS, PARENTS, TEACHERS, CLASSES
from app.mock_api import attendance as attendance_service
from app.mock_api import escalation as escalation_service
from app.mock_api.attendance import ForbiddenError, NotFoundError, BadRequestError
from app.mock_api.escalation import ForbiddenError as EscForbidden, NotFoundError as EscNotFound


def _format_records(records) -> str:
    if not records:
        return "No attendance records found."
    lines = [f"{r.date.isoformat()}: {r.status.value}" for r in records]
    present = len([r for r in records if r.status == AttendanceStatus.PRESENT])
    pct = round(present / len(records) * 100, 1)
    return f"Attendance rate: {pct}% ({present}/{len(records)} days present).\nDetails:\n" + "\n".join(lines)


def _resolve_child(current_user: CurrentUser, child_name: str) -> str | None:
    parent = PARENTS.get(current_user.profile_id)
    if parent is None:
        return None
    name_lower = child_name.strip().lower()
    for sid in parent.child_ids:
        student = STUDENTS.get(sid)
        if student and name_lower in student.name.lower():
            return sid
    return None


def _resolve_student_in_teachers_classes(current_user: CurrentUser, student_name: str) -> str | None:
    teacher = TEACHERS.get(current_user.profile_id)
    if teacher is None:
        return None
    name_lower = student_name.strip().lower()
    for class_id in teacher.class_ids:
        classroom = CLASSES.get(class_id)
        if classroom is None:
            continue
        for sid in classroom.student_ids:
            student = STUDENTS.get(sid)
            if student and name_lower in student.name.lower():
                return sid
    return None


def build_tools_for_user(current_user: CurrentUser) -> list:
    tools = []

    if current_user.role == Role.STUDENT:
        @tool
        def get_my_attendance() -> str:
            """Get the current logged-in student's own attendance record. Use this whenever the student asks about their attendance."""
            try:
                records = attendance_service.get_student_attendance(current_user, current_user.profile_id)
            except (ForbiddenError, NotFoundError) as e:
                return f"Error: {e}"
            return _format_records(records)

        tools.append(get_my_attendance)

    if current_user.role == Role.PARENT:
        @tool
        def list_my_children() -> str:
            """List the names of the parent's children registered at this school. Call this FIRST if the parent has not specified which child they mean and you don't know how many children they have."""
            parent = PARENTS.get(current_user.profile_id)
            if not parent or not parent.child_ids:
                return "No children found linked to your account."
            names = [STUDENTS[sid].name for sid in parent.child_ids if sid in STUDENTS]
            return ", ".join(names)

        @tool
        def get_child_attendance(child_name: str) -> str:
            """Get attendance for one of the parent's children, identified by first name. If the parent has multiple children and hasn't said which one, call list_my_children first and ASK the parent to clarify — do not guess."""
            student_id = _resolve_child(current_user, child_name)
            if student_id is None:
                return f"Error: no child named '{child_name}' is linked to your account. Use list_my_children to see valid names."
            try:
                records = attendance_service.get_student_attendance(current_user, student_id)
            except (ForbiddenError, NotFoundError) as e:
                return f"Error: {e}"
            return _format_records(records)

        tools.extend([list_my_children, get_child_attendance])

    if current_user.role == Role.TEACHER:
        @tool
        def mark_student_attendance(student_name: str, status: str) -> str:
            """Mark today's attendance for a student in one of the teacher's own classes. status must be exactly 'present', 'absent', or 'late'."""
            student_id = _resolve_student_in_teachers_classes(current_user, student_name)
            if student_id is None:
                return f"Error: no student named '{student_name}' found in your classes."
            try:
                status_enum = AttendanceStatus(status.strip().lower())
            except ValueError:
                return "Error: status must be 'present', 'absent', or 'late'."
            student = STUDENTS[student_id]
            try:
                attendance_service.mark_class_attendance(
                    current_user, student.class_id, [(student_id, status_enum)]
                )
            except (ForbiddenError, NotFoundError, BadRequestError) as e:
                return f"Error: {e}"
            return f"Marked {student.name} as {status_enum.value} for today."

        @tool
        def get_class_student_attendance(student_name: str) -> str:
            """View attendance history for a specific student in one of the teacher's own classes."""
            student_id = _resolve_student_in_teachers_classes(current_user, student_name)
            if student_id is None:
                return f"Error: no student named '{student_name}' found in your classes."
            try:
                records = attendance_service.get_student_attendance(current_user, student_id)
            except (ForbiddenError, NotFoundError) as e:
                return f"Error: {e}"
            return _format_records(records)

        tools.extend([mark_student_attendance, get_class_student_attendance])

    if current_user.role == Role.PRINCIPAL:
        @tool
        def get_school_attendance_summary() -> str:
            """Get overall school-wide attendance analytics, broken down by class."""
            try:
                summary = attendance_service.get_school_attendance_summary(current_user)
            except ForbiddenError as e:
                return f"Error: {e}"
            lines = [f"Overall attendance rate: {summary['overall_attendance_rate']}%"]
            for cid, stats in summary["by_class"].items():
                lines.append(f"- {stats['class_name']}: {stats['attendance_rate']}%")
            return "\n".join(lines)

        tools.append(get_school_attendance_summary)

    @tool
    def request_escalation(escalate_to: str, reason: str) -> str:
        """Create a PENDING request to escalate this conversation to a real teacher or school management. escalate_to must be 'teacher' or 'management'. This does NOT notify anyone yet — you MUST ask the user to confirm, then call confirm_escalation with the returned request_id. Never tell the user the request was submitted until confirm_escalation succeeds."""
        target_role = Role.TEACHER if escalate_to.strip().lower() == "teacher" else Role.PRINCIPAL
        try:
            req = escalation_service.create_escalation_request(current_user, target_role, reason)
        except (EscForbidden, EscNotFound, ValueError) as e:
            return f"Error: {e}"
        return f"Pending escalation created with request_id={req.id}, targeting {escalate_to}. Ask the user to confirm before calling confirm_escalation."

    @tool
    def confirm_escalation(request_id: str) -> str:
        """Confirm a pending escalation request after the user has explicitly said yes. Only call this after the user confirms — never before."""
        try:
            req = escalation_service.confirm_escalation(current_user, request_id)
        except (EscForbidden, EscNotFound) as e:
            return f"Error: {e}"
        return f"Escalation request {req.id} has been confirmed and submitted to {req.target_role.value}."

    tools.extend([request_escalation, confirm_escalation])

    return tools