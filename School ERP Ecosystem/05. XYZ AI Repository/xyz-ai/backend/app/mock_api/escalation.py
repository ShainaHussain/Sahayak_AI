"""
Escalation mock API.

Deliberately two-step (create pending -> confirm) rather than one call,
because the assessment explicitly states: "must not claim that a teacher
or school management representative has been contacted unless the
call/request is actually confirmed." A single-step "escalate" tool would
make it too easy for the LLM to say "done" without a real confirmation
step existing to check against.
"""

from uuid import uuid4

from app.auth.dependencies import CurrentUser
from app.models.schemas import EscalationRequest, Role
from app.models.seed_data import TEACHERS, PRINCIPALS, STUDENTS, PARENTS, CLASSES

ESCALATIONS: dict[str, EscalationRequest] = {}


class ForbiddenError(Exception):
    pass


class NotFoundError(Exception):
    pass


def create_escalation_request(
    current_user: CurrentUser,
    target_role: Role,
    reason: str,
) -> EscalationRequest:
    if target_role not in (Role.TEACHER, Role.PRINCIPAL):
        raise ValueError("Escalation target must be a teacher or the principal")

    if target_role == Role.TEACHER:
        if current_user.role == Role.STUDENT:
            student = STUDENTS.get(current_user.profile_id)
        elif current_user.role == Role.PARENT:
            parent = PARENTS.get(current_user.profile_id)
            student = STUDENTS.get(parent.child_ids[0]) if parent and parent.child_ids else None
        else:
            raise ForbiddenError("Only students and parents can escalate to a teacher")

        if student is None:
            raise NotFoundError("Could not resolve a student record to find the teacher")

        classroom = CLASSES.get(student.class_id)
        target_id = classroom.teacher_id if classroom else None
        if target_id is None or target_id not in TEACHERS:
            raise NotFoundError("Could not resolve a teacher for this student's class")

    else:  # PRINCIPAL
        target_id = next(iter(PRINCIPALS.keys()), None)
        if target_id is None:
            raise NotFoundError("No principal is registered in the system")

    request = EscalationRequest(
        id=str(uuid4()),
        requested_by=current_user.user_id,
        target_role=target_role,
        target_id=target_id,
        reason=reason,
        status="pending",
    )
    ESCALATIONS[request.id] = request
    return request


def confirm_escalation(current_user: CurrentUser, request_id: str) -> EscalationRequest:
    request = ESCALATIONS.get(request_id)
    if request is None:
        raise NotFoundError(f"No escalation request with id {request_id}")

    if request.requested_by != current_user.user_id:
        raise ForbiddenError("This escalation request does not belong to you")

    if request.status == "confirmed":
        return request

    request.status = "confirmed"
    return request