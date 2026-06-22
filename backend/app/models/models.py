from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid7

from pydantic import EmailStr
from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    tutor = "tutor"
    student = "student"


class CompletionStatus(str, Enum):
    complete = "complete"
    progress = "progress"
    pending = "pending"


class GradesStatus(str, Enum):
    passed = "passed"
    failed = "failed"


class RefreshTokens(SQLModel, table=True):
    id: UUID | None = Field(default_factory=uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    revoked: bool = False
    role: UserRole
    token_hash: str
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class CohortEnrollment(SQLModel, table=True):
    cohort_id: UUID = Field(foreign_key="cohorts.id", primary_key=True)
    student_id: UUID = Field(foreign_key="users.id", primary_key=True)


class Users(SQLModel, table=True):
    id: UUID | None = Field(default_factory=uuid7, primary_key=True)
    username: str = Field()
    password: str
    email: EmailStr = Field(unique=True)
    role: UserRole
    tutor_cohort: Optional["Cohorts"] = Relationship(back_populates="tutor")
    student_cohorts: list["Cohorts"] | None = Relationship(
        back_populates="students", link_model=CohortEnrollment
    )
    submissions: list["Submissions"] | None = Relationship(back_populates="student")


class Assignments(SQLModel, table=True):
    id: UUID | None = Field(default_factory=uuid7, primary_key=True)
    title: str
    description: str
    curriculum_id: UUID = Field(foreign_key="curriculum.id")
    deadline: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    curriculum: "Curriculum" = Relationship(back_populates="assignments")
    submissions: list["Submissions"] = Relationship(back_populates="assignment")
    solution: Optional["Solutions"] = Relationship(back_populates="assignment")


class Curriculum(SQLModel, table=True):
    id: UUID | None = Field(default_factory=uuid7, primary_key=True)
    cohort_id: UUID = Field(foreign_key="cohorts.id")
    title: str
    description: str
    completion_status: CompletionStatus
    assignments: list["Assignments"] = Relationship(back_populates="curriculum")
    cohort: "Cohorts" = Relationship(back_populates="curriculum")
    order: int = Field(ge=0)


class Cohorts(SQLModel, table=True):
    id: UUID | None = Field(default_factory=uuid7, primary_key=True)
    name: str
    description: str
    tutor_id: UUID = Field(foreign_key="users.id")
    curriculum: list["Curriculum"] | None = Relationship(back_populates="cohort")
    tutor: Users = Relationship(back_populates="tutor_cohort")
    students: list["Users"] | None = Relationship(
        back_populates="student_cohorts", link_model=CohortEnrollment
    )


class Submissions(SQLModel, table=True):
    id: UUID | None = Field(default_factory=uuid7, primary_key=True)
    assignment_id: UUID = Field(foreign_key="assignments.id")
    student_id: UUID = Field(foreign_key="users.id")
    student: Users = Relationship(back_populates="submissions")
    assignment: "Assignments" = Relationship(back_populates="submissions")
    name: str
    submission: str
    submitted_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class Grades(SQLModel, table=True):
    id: UUID | None = Field(default_factory=uuid7, primary_key=True)
    submission_id: UUID = Field(foreign_key="submissions.id")
    status: GradesStatus
    score: int = Field(le=10, ge=0)
    feedback: str | None


class Solutions(SQLModel, table=True):
    id: UUID | None = Field(default_factory=uuid7, primary_key=True)
    assignment_id: UUID = Field(foreign_key="assignments.id")
    content: str
    assignment: Assignments = Relationship(back_populates="solution")
