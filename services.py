# """
# services.py
# -----------
# All business logic lives here:
#   1. generate_tasks_from_llm  – calls Groq API asynchronously
#   2. distribute_tasks          – smart assignment algorithm
# """

# import os
# import json
# import copy
# from typing import List, Optional, Tuple

# import httpx
# from dotenv import load_dotenv

# from models import GeneratedTask, TeamMember, AssignedTask
# from utils import MOCK_TEAM_MEMBERS, extract_json_from_text, compute_match_score

# load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
# GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


# # ── 1. AI Task Generation ─────────────────────────────────────────────────────

# SYSTEM_PROMPT = """You are a senior software architect and project manager.
# Given a project description, break it down into actionable development tasks.

# For each task return a JSON object with EXACTLY these fields:
#   - Task_Name       (string)  : concise task title
#   - Description     (string)  : what needs to be done (1–3 sentences)
#   - Required_Skills (array)   : list of skill strings (e.g. ["Python", "FastAPI"])
#   - Difficulty_Level (integer): 1 (trivial) – 10 (expert)

# Return ONLY a valid JSON array of these objects. No prose, no markdown fences,
# no commentary — pure JSON starting with [ and ending with ]."""


# async def generate_tasks_from_llm(
#     project_description: str,
#     num_tasks: Optional[int] = None,
# ) -> List[GeneratedTask]:
#     """
#     Sends the project description to Groq and returns a validated list of
#     GeneratedTask objects.
#     """
#     if not GROQ_API_KEY:
#         raise EnvironmentError(
#             "GROQ_API_KEY is not set. Add it to your .env file."
#         )

#     user_message = project_description
#     if num_tasks:
#         user_message += f"\n\nGenerate exactly {num_tasks} tasks."

#     payload = {
#         "model": GROQ_MODEL,
#         "messages": [
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": user_message},
#         ],
#         "temperature": 0.4,
#         "max_tokens": 2048,
#     }

#     headers = {
#         "Authorization": f"Bearer {GROQ_API_KEY}",
#         "Content-Type": "application/json",
#     }

#     async with httpx.AsyncClient(timeout=60.0) as client:
#         response = await client.post(GROQ_ENDPOINT, json=payload, headers=headers)
#         response.raise_for_status()

#     raw_content: str = response.json()["choices"][0]["message"]["content"]

#     # Parse and validate via Pydantic
#     raw_list = extract_json_from_text(raw_content)
#     tasks = [GeneratedTask(**item) for item in raw_list]
#     return tasks


# # ── 2. Smart Task Distribution ────────────────────────────────────────────────

# def distribute_tasks(
#     tasks: List[GeneratedTask],
#     team: Optional[List[TeamMember]] = None,
# ) -> Tuple[List[AssignedTask], List[GeneratedTask]]:
#     """
#     Assigns each task to the best-matching team member using a greedy
#     skill-match + workload-balance strategy.

#     Algorithm
#     ---------
#     For each task (sorted hardest-first so critical tasks are placed first):
#       1. Score every member by skill overlap with the task's Required_Skills.
#       2. Among members with the highest score, prefer the one with the
#          lowest current_workload (load balancing).
#       3. Assign if the best score > 0; otherwise add to unassigned.

#     Returns
#     -------
#     (assigned_tasks, unassigned_tasks)
#     """
#     if team is None:
#         team = copy.deepcopy(MOCK_TEAM_MEMBERS)
#     else:
#         team = copy.deepcopy(team)  # avoid mutating caller's list

#     assigned: List[AssignedTask] = []
#     unassigned: List[GeneratedTask] = []

#     # Process hardest tasks first — they are hardest to place
#     sorted_tasks = sorted(tasks, key=lambda t: t.Difficulty_Level, reverse=True)

#     for task in sorted_tasks:
#         best_member: Optional[TeamMember] = None
#         best_score: float = 0.0

#         for member in team:
#             score = compute_match_score(task.Required_Skills, member.skills)
#             if score > best_score or (
#                 score == best_score
#                 and best_member is not None
#                 and member.current_workload < best_member.current_workload
#             ):
#                 best_score = score
#                 best_member = member

#         if best_member is None or best_score == 0.0:
#             unassigned.append(task)
#             continue

#         # Build a human-readable reason
#         matched = sorted(
#             {s.lower() for s in task.Required_Skills}
#             & {s.lower() for s in best_member.skills}
#         )
#         reason = (
#             f"{best_member.name} matches {int(best_score * 100)}% of required skills "
#             f"({', '.join(matched) or 'general fit'}) "
#             f"and has {best_member.current_workload} task(s) already assigned."
#         )

#         assigned.append(
#             AssignedTask(
#                 task=task,
#                 assigned_to=best_member.name,
#                 member_id=best_member.id,
#                 match_score=round(best_score, 2),
#                 reason=reason,
#             )
#         )
#         best_member.current_workload += 1

#     return assigned, unassigned
"""
services.py
-----------
All business logic lives here:
  1. generate_tasks_from_llm  – calls Groq API asynchronously
  2. distribute_tasks          – smart assignment algorithm
"""

import os
import copy
from typing import List, Optional, Tuple

import httpx
from dotenv import load_dotenv

from models import GeneratedTask, TeamMember, AssignedTask
from utils import extract_json_from_text, compute_match_score

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


# ── 1. AI Task Generation ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior software architect and project manager.
Given a project description, break it down into actionable development tasks.

For each task return a JSON object with EXACTLY these fields:
  - Task_Name       (string)  : concise task title
  - Description     (string)  : what needs to be done (1–3 sentences)
  - Required_Skills (array)   : list of skill strings (e.g. ["Python", "FastAPI"])
  - Difficulty_Level (integer): 1 (trivial) – 10 (expert)

Return ONLY a valid JSON array of these objects. No prose, no markdown fences,
no commentary — pure JSON starting with [ and ending with ]."""


async def generate_tasks_from_llm(
    project_description: str,
    num_tasks: Optional[int] = None,
) -> List[GeneratedTask]:
    """
    Sends the project description to Groq and returns a validated list of
    GeneratedTask objects.
    """
    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your .env file."
        )

    user_message = project_description
    if num_tasks:
        user_message += f"\n\nGenerate exactly {num_tasks} tasks."

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.4,
        "max_tokens": 2048,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(GROQ_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()

    raw_content: str = response.json()["choices"][0]["message"]["content"]

    # Parse and validate via Pydantic
    raw_list = extract_json_from_text(raw_content)
    tasks = [GeneratedTask(**item) for item in raw_list]
    return tasks


# ── 2. Smart Task Distribution ────────────────────────────────────────────────

def distribute_tasks(
    tasks: List[GeneratedTask],
    team: List[TeamMember],
) -> Tuple[List[AssignedTask], List[GeneratedTask]]:
    """
    Assigns each task to the best-matching team member using a greedy
    skill-match + workload-balance strategy.

    Algorithm
    ---------
    For each task (sorted hardest-first so critical tasks are placed first):
      1. Score every member by skill overlap with the task's Required_Skills.
      2. Among members with the highest score, prefer the one with the
         lowest current_workload (load balancing).
      3. Assign if the best score > 0; otherwise add to unassigned.

    Returns
    -------
    (assigned_tasks, unassigned_tasks)
    """
    team = copy.deepcopy(team)  # avoid mutating caller's list

    assigned: List[AssignedTask] = []
    unassigned: List[GeneratedTask] = []

    # Process hardest tasks first — they are hardest to place
    sorted_tasks = sorted(tasks, key=lambda t: t.Difficulty_Level, reverse=True)

    for task in sorted_tasks:
        best_member: Optional[TeamMember] = None
        best_score: float = 0.0

        for member in team:
            score = compute_match_score(task.Required_Skills, member.skills)
            if score > best_score or (
                score == best_score
                and best_member is not None
                and member.current_workload < best_member.current_workload
            ):
                best_score = score
                best_member = member

        if best_member is None or best_score == 0.0:
            unassigned.append(task)
            continue

        # Build a human-readable reason
        matched = sorted(
            {s.lower() for s in task.Required_Skills}
            & {s.lower() for s in best_member.skills}
        )
        reason = (
            f"{best_member.name} matches {int(best_score * 100)}% of required skills "
            f"({', '.join(matched) or 'general fit'}) "
            f"and has {best_member.current_workload} task(s) already assigned."
        )

        assigned.append(
            AssignedTask(
                task=task,
                assigned_to=best_member.name,
                member_id=best_member.id,
                match_score=round(best_score, 2),
                reason=reason,
            )
        )
        best_member.current_workload += 1

    return assigned, unassigned