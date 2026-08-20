"""
Core data models for XYZ AI.

Design rules (do not violate these when extending):
1. Every relationship is stored on BOTH sides (e.g. Parent.child_ids AND
   Student.parent_ids) so authorization checks never need to guess a
   reverse lookup — they read the direction that matches the question
   being asked ("can this parent see this student?" reads parent.child_ids).
2. IDs are strings (not ints) to avoid accidental arithmetic/index bugs
   and to match what a real DB (Supabase/Postgres UUID) would return.
3. No model here talks to a DB or API — this file is pure data shape.
"""

from enum import Enum
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field


class Role(str, Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    PRINCIPAL = "principal"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"


# ---------------------------------------------------------------------------
# Role profiles — one per role, holding only that role's relevant data.
# ---------------------------------------------------------------------------

class Student(BaseModel):
    id: str
    name: str
    class_id: str
    parent_ids: List[str] = Field(default_factory=list)  # usually 1, sometimes 2 (both parents registered)


class Parent(BaseModel):
    id: str
    name: str
    child_ids: List[str] = Field(default_factory=list)  # can be >1 (siblings at same school)


class Teacher(BaseModel):
    id: str
    name: str
    class_ids: List[str] = Field(default_factory=list)  # a teacher may teach multiple classes


class Principal(BaseModel):
    id: str
    name: str


class ClassRoom(BaseModel):
    id: str
    name: str
    teacher_id: str
    student_ids: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Auth account — separate from the role profile on purpose.
# Login/password concerns should never be mixed into domain data.
# ---------------------------------------------------------------------------

class UserAccount(BaseModel):
    id: str
    username: str
    password_hash: str
    role: Role
    profile_id: str  # points to the matching Student/Parent/Teacher/Principal.id


# ---------------------------------------------------------------------------
# Domain records
# ---------------------------------------------------------------------------

class AttendanceRecord(BaseModel):
    id: str
    student_id: str
    date: date
    status: AttendanceStatus
    marked_by: str  # teacher_id — every record must be traceable to who marked it


class EscalationRequest(BaseModel):
    id: str
    requested_by: str  # user_id (parent or student)
    target_role: Role  # TEACHER or PRINCIPAL
    target_id: str      # specific teacher_id or principal_id
    reason: Optional[str] = None
    status: str = "pending"  # pending -> confirmed -> completed (mock only, no real call)
