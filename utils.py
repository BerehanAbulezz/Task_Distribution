"""
utils.py
--------
Utility helpers + the mock team-member database used for testing.
"""

import json
import re
from typing import List

from models import TeamMember


# ── Mock Team-Member Database ────────────────────────────────────────────────
# Replace / extend this list with real DB calls in production.

MOCK_TEAM_MEMBERS: List[TeamMember] = [
    TeamMember(
        id=1,
        name="Omar Farhan",
        skills=["Project Management", "Stakeholder Management", "Communication", "Agile"],
        current_workload=0,
    ),
    TeamMember(
        id=2,
        name="Ahmed Moataz",
        skills=["Database Design", "MySQL", "SQL", "PostgreSQL", "MongoDB"],
        current_workload=0,
    ),
    TeamMember(
        id=3,
        name="Jana Walid",
        skills=["HTML", "CSS", "JavaScript", "React", "Next.js", "Tailwind CSS"],
        current_workload=0,
    ),
    TeamMember(
        id=4,
        name="Omar Magdy",
        skills=["Node.js", "Express", "API Design", "REST", "FastAPI", "Python"],
        current_workload=0,
    ),
    TeamMember(
        id=5,
        name="Habiba Ahmed",
        skills=["JavaScript", "Node.js", "MySQL", "Testing", "Jest", "Enzyme"],
        current_workload=0,
    ),
    TeamMember(
        id=6,
        name="Berehan Abuelezz",
        skills=["DevOps", "AWS", "Docker", "CI/CD", "Linux", "Kubernetes"],
        current_workload=0,
    ),
    TeamMember(
        id=7,
        name="Hager Mohammed",
        skills=["Python", "FastAPI", "Machine Learning", "AI", "Passport.js", "Node.js"],
        current_workload=0,
    ),
    TeamMember(
        id=8,
        name="Omar Madkour",
        skills=["JavaScript", "React", "Node.js", "SQL", "Communication"],
        current_workload=0,
    ),
]


# ── JSON Extraction Helper ────────────────────────────────────────────────────

def extract_json_from_text(text: str) -> list:
    """
    Robustly extract a JSON array from an LLM response that may contain
    markdown fences, prose preamble, or trailing commentary.
    """
    # 1. Try to strip ```json … ``` fences
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    # 2. Find the first '[' … last ']' in the raw text
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start: end + 1])

    raise ValueError("No valid JSON array found in LLM response.")


# ── Skill-Match Scorer ────────────────────────────────────────────────────────

def compute_match_score(required_skills: List[str], member_skills: List[str]) -> float:
    """
    Returns a score between 0 and 1 representing what fraction of the
    required skills a team member covers (case-insensitive).
    """
    if not required_skills:
        return 0.0

    required_lower = {s.lower() for s in required_skills}
    member_lower = {s.lower() for s in member_skills}
    matched = required_lower & member_lower
    return len(matched) / len(required_lower)
