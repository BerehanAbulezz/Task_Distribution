from pydantic import BaseModel, Field
from typing import List, Optional


# ── Request Models ──────────────────────────────────────────────────────────

class ProjectDescriptionRequest(BaseModel):
    """Request body for AI task generation."""
    project_description: str = Field(
        ...,
        min_length=20,
        description="A detailed description of the project to generate tasks for.",
        examples=["Build a student attendance and grading system with a web dashboard."]
    )
    num_tasks: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Optional: how many tasks to generate (1–20). Defaults to LLM judgment."
    )


class DistributionRequest(BaseModel):
    """Request body for smart task distribution."""
    tasks: List["GeneratedTask"] = Field(
        ...,
        description="List of tasks (as returned by /generate-tasks) to distribute."
    )


# ── Core Domain Models ───────────────────────────────────────────────────────

class GeneratedTask(BaseModel):
    """A single AI-generated task."""
    Task_Name: str = Field(..., description="Short name of the task.")
    Description: str = Field(..., description="What needs to be done.")
    Required_Skills: List[str] = Field(..., description="Skills needed for this task.")
    Difficulty_Level: int = Field(..., ge=1, le=10, description="Difficulty score 1–10.")


class TeamMember(BaseModel):
    """A member of the project team."""
    id: int
    name: str
    skills: List[str] = Field(..., description="Skills this member has.")
    current_workload: int = Field(
        default=0,
        ge=0,
        description="Number of tasks already assigned."
    )


class AssignedTask(BaseModel):
    """A task after it has been assigned to a team member."""
    task: GeneratedTask
    assigned_to: str = Field(..., description="Name of the assigned team member.")
    member_id: int
    match_score: float = Field(..., description="Skill match percentage (0–1).")
    reason: str = Field(..., description="Human-readable reason for the assignment.")


# ── Response Models ──────────────────────────────────────────────────────────

class TaskGenerationResponse(BaseModel):
    """Response returned by /generate-tasks."""
    project_description: str
    total_tasks: int
    tasks: List[GeneratedTask]


class DistributionResponse(BaseModel):
    """Response returned by /distribute-tasks."""
    total_tasks: int
    assigned_tasks: List[AssignedTask]
    unassigned_tasks: List[GeneratedTask] = Field(
        default_factory=list,
        description="Tasks that could not be matched to any team member."
    )
    distribution_summary: dict = Field(
        default_factory=dict,
        description="How many tasks each member received."
    )


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "Syntra.AI Task Microservice"
    version: str = "1.0.0"
