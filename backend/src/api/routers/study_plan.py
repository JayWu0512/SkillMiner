from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

from src.db.supabase_client import get_supabase_client
from src.llm.client import get_openai_client

router = APIRouter()


HARD_SKILLS = [
    "javascript", "typescript", "react", "node.js", "python", "java", "sql",
    "aws", "docker", "kubernetes", "git", "rest apis", "graphql", "mongodb",
    "postgresql", "machine learning", "data analysis", "agile", "ci/cd", "tdd",
    "tableau", "power bi", "statistics", "pandas", "numpy", "scikit-learn",
    "excel", "data visualization"
]

SOFT_SKILLS = [
    "leadership", "communication", "team collaboration", "problem solving",
    "critical thinking", "time management", "adaptability", "creativity",
    "conflict resolution", "emotional intelligence", "presentation skills",
    "mentoring", "strategic thinking", "decision making"
]


class StudyPlanRequest(BaseModel):
    analysis_id: str = Field(..., alias="analysisId")
    hours_per_day: str = Field(..., alias="hoursPerDay")
    timeline: int
    study_days: List[str] = Field(..., alias="studyDays")

    @validator("timeline")
    def validate_timeline(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("timeline must be greater than 0")
        if value > 365:
            raise ValueError("timeline cannot exceed 365 days")
        return value

    @validator("study_days")
    def validate_study_days(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("studyDays cannot be empty")
        return value


class StudyPlanResponse(BaseModel):
    id: str
    planId: str
    userId: Optional[str]
    analysisId: str
    status: str
    createdAt: str
    updatedAt: str
    startDate: str
    endDate: str
    totalDays: int
    hoursPerDay: str
    studyDays: List[str]
    metadata: Dict[str, Any]
    planData: Dict[str, Any]


def _extract_skills(text: str, skills: List[str]) -> List[str]:
    text_lower = text.lower()
    return [skill.title() for skill in skills if skill.lower() in text_lower]


def _build_analysis_context(row: Dict[str, Any]) -> Dict[str, Any]:
    resume_text: str = row.get("resume_text") or ""
    job_description: str = row.get("job_description") or ""

    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume text is missing for this analysis")

    if not job_description:
        raise HTTPException(status_code=400, detail="Job description is missing for this analysis")

    hard_skills_resume = _extract_skills(resume_text, HARD_SKILLS)
    soft_skills_resume = _extract_skills(resume_text, SOFT_SKILLS)

    required_hard = _extract_skills(job_description, HARD_SKILLS)
    required_soft = _extract_skills(job_description, SOFT_SKILLS)

    matching_hard = [skill for skill in hard_skills_resume if skill in required_hard]
    matching_soft = [skill for skill in soft_skills_resume if skill in required_soft]

    missing_hard = [skill for skill in required_hard if skill not in matching_hard]
    missing_soft = [skill for skill in required_soft if skill not in matching_soft]

    total_required = len(required_hard) + len(required_soft)
    total_matched = len(matching_hard) + len(matching_soft)

    if row.get("match_score") is not None:
        match_score = int(round(float(row["match_score"])))
    else:
        match_score = math.floor((total_matched / total_required) * 100) if total_required else 0

    return {
        "user_id": row.get("user_id"),
        "analysis_id": row.get("id"),
        "match_score": match_score,
        "job_description": job_description,
        "resume_text": resume_text,
        "matching_hard_skills": matching_hard,
        "matching_soft_skills": matching_soft,
        "missing_hard_skills": missing_hard,
        "missing_soft_skills": missing_soft,
    }


def _call_openai_for_plan(
    context: Dict[str, Any],
    hours_per_day: str,
    timeline: int,
    study_days: List[str],
) -> Optional[Dict[str, Any]]:
    try:
        client = get_openai_client()
    except RuntimeError:
        return None

    system_prompt = (
        "You are an expert career development mentor. Create a detailed, day-by-day study plan "
        "that helps a candidate close their skill gaps for a target job. The plan must be practical, "
        "balanced, and motivating."
    )

    user_prompt = f"""
Target Job Description:
{context["job_description"][:2000]}

Candidate Resume Excerpt:
{context["resume_text"][:2000]}

Current Skills:
- Hard Skills: {', '.join(context["matching_hard_skills"]) or 'None'}
- Soft Skills: {', '.join(context["matching_soft_skills"]) or 'None'}

Skill Gaps To Close:
- Hard Skills: {', '.join(context["missing_hard_skills"]) or 'None'}
- Soft Skills: {', '.join(context["missing_soft_skills"]) or 'None'}

Availability:
- Hours per day: {hours_per_day}
- Study days per week: {', '.join(study_days)}
- Timeline: {timeline} days

Create a {timeline}-day study plan. Output JSON with this structure:
{{
  "skills": [
    {{"name": "...", "priority": "High/Medium/Low", "estimatedTime": "12 hours", "resources": ["Resource 1", "Resource 2"]}}
  ],
  "tasks": [
    {{
      "dayOfWeek": "Mon",
      "theme": "Foundations",
      "task": "Study topic",
      "resources": "Resource name",
      "estTime": "2h",
      "xp": 40
    }}
  ],
  "phases": [
    {{"range": [0, 6], "label": "Foundations", "color": "purple"}}
  ],
  "summary": {{
    "totalXP": 600,
    "totalHours": 80,
    "currentProgress": 0
  }}
}}

Important:
- Provide exactly {timeline} tasks (one per day).
- Ensure tasks gradually increase in difficulty.
- Include review/reflection days.
- XP per task must be between 20 and 120.
- Keep JSON valid.
""".strip()

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[StudyPlan] OpenAI request failed: {exc}")
        return None

    try:
        content = completion.choices[0].message.content if completion.choices else "{}"
        return json.loads(content or "{}")
    except (ValueError, AttributeError, IndexError) as exc:
        print(f"[StudyPlan] Failed to parse OpenAI response: {exc}")
        return None


def _generate_mock_plan(
    context: Dict[str, Any],
    hours_per_day: str,
    timeline: int,
) -> Dict[str, Any]:
    themes = [
        "Foundations",
        "Core Skills",
        "Applied Practice",
        "Project Work",
        "Review & Reflection",
    ]

    tasks: List[Dict[str, Any]] = []
    start_date = datetime.utcnow().date()
    for index in range(timeline):
        day = start_date + timedelta(days=index)
        theme = themes[index % len(themes)]
        tasks.append(
            {
                "date": day.strftime("%b %d"),
                "fullDate": day.isoformat(),
                "dayOfWeek": day.strftime("%a"),
                "theme": theme,
                "task": f"{theme}: Focused learning session {index + 1}",
                "resources": "SkillMiner Recommended Resources",
                "estTime": hours_per_day,
                "xp": 40 + (index % 5) * 10,
                "completed": False,
            }
        )

    skills = [
        {
            "name": skill,
            "priority": "High",
            "estimatedTime": "12 hours",
            "resources": ["Official Documentation", "Recommended Course"],
        }
        for skill in context.get("missing_hard_skills", [])[:5]
    ]

    summary = {
        "totalXP": sum(task["xp"] for task in tasks),
        "totalHours": timeline * max(1, _parse_hours_from_estimate(hours_per_day)),
        "currentProgress": 0,
    }

    phases = [
        {"range": [0, max(0, timeline // 4)], "label": "Foundations", "color": "purple"},
        {"range": [max(0, timeline // 4) + 1, max(0, timeline // 2)], "label": "Intermediate", "color": "blue"},
        {"range": [max(0, timeline // 2) + 1, max(0, (timeline * 3) // 4)], "label": "Advanced", "color": "orange"},
        {"range": [max(0, (timeline * 3) // 4) + 1, timeline - 1], "label": "Portfolio", "color": "green"},
    ]

    return {
        "skills": skills,
        "tasks": tasks,
        "phases": phases,
        "summary": summary,
    }


def _normalise_plan(
    plan: Dict[str, Any],
    hours_per_day: str,
    timeline: int,
) -> Dict[str, Any]:
    tasks: List[Dict[str, Any]] = plan.get("tasks") or []
    study_days = []

    # Ensure exactly timeline tasks
    if len(tasks) < timeline:
        last_known_day = datetime.utcnow().date()
        if tasks:
            try:
                last_known_day = datetime.strptime(tasks[-1].get("fullDate", ""), "%Y-%m-%d").date()
            except ValueError:
                pass
        for index in range(len(tasks), timeline):
            day = last_known_day + timedelta(days=index - len(tasks) + 1)
            tasks.append(
                {
                    "date": day.strftime("%b %d"),
                    "fullDate": day.isoformat(),
                    "dayOfWeek": day.strftime("%a"),
                    "theme": "Focused Study",
                    "task": f"Deep practice session {index + 1}",
                    "resources": "Curated learning resources",
                    "estTime": hours_per_day,
                    "xp": 60,
                    "completed": False,
                }
            )
    elif len(tasks) > timeline:
        tasks = tasks[:timeline]

    normalised_tasks: List[Dict[str, Any]] = []
    start_date = datetime.utcnow().date()
    for index, task in enumerate(tasks):
        day = start_date + timedelta(days=index)
        resources_field = task.get("resources")
        if isinstance(resources_field, list):
            resources = ", ".join(resources_field)
        else:
            resources = resources_field or "Suggested resources"

        est_time = task.get("estTime") or task.get("estimatedTime") or hours_per_day
        xp_value = task.get("xp")
        try:
            xp_int = int(xp_value)
        except (TypeError, ValueError):
            xp_int = 60

        normalised_tasks.append(
            {
                "date": day.strftime("%b %d"),
                "fullDate": day.isoformat(),
                "dayOfWeek": task.get("dayOfWeek") or day.strftime("%a"),
                "theme": task.get("theme") or "Focused Study",
                "task": task.get("task") or task.get("description") or "Learning task",
                "resources": resources,
                "estTime": est_time,
                "xp": xp_int,
                "completed": bool(task.get("completed", False)),
            }
        )
        study_days.append(normalised_tasks[-1]["dayOfWeek"])

    phases = plan.get("phases") or []
    if not phases:
        phases = [
            {"range": [0, max(0, timeline // 3)], "label": "Foundations", "color": "purple"},
            {"range": [max(0, timeline // 3) + 1, max(0, (timeline * 2) // 3)], "label": "Application", "color": "blue"},
            {"range": [max(0, (timeline * 2) // 3) + 1, timeline - 1], "label": "Project", "color": "green"},
        ]

    skills = plan.get("skills") or []
    if isinstance(skills, list):
        cleaned_skills: List[Dict[str, Any]] = []
        for skill in skills:
            if isinstance(skill, dict):
                resources_field = skill.get("resources")
                if isinstance(resources_field, list):
                    resources_clean = [str(res) for res in resources_field]
                elif isinstance(resources_field, str):
                    resources_clean = [resources_field]
                else:
                    resources_clean = []
                cleaned_skills.append(
                    {
                        "name": skill.get("name") or "Skill",
                        "priority": skill.get("priority") or "Medium",
                        "estimatedTime": skill.get("estimatedTime") or "10 hours",
                        "resources": resources_clean,
                    }
                )
        skills = cleaned_skills
    else:
        skills = []

    summary = plan.get("summary") or {}
    total_xp = sum(task["xp"] for task in normalised_tasks)
    total_hours = sum(_parse_hours_from_estimate(task["estTime"]) for task in normalised_tasks)

    summary.setdefault("totalXP", total_xp)
    summary.setdefault("totalHours", total_hours)
    summary.setdefault("currentProgress", 0)

    return {
        "skills": skills,
        "tasks": normalised_tasks,
        "phases": phases,
        "summary": summary,
    }


def _parse_hours_from_estimate(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        return 1
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return 1
    return max(1, int(digits))


def _format_study_plan_response(record: Dict[str, Any]) -> StudyPlanResponse:
    plan_data = record.get("plan_data") or {}
    metadata = record.get("metadata") or {}

    # Convert metadata to expected defaults
    total_tasks = len(plan_data.get("tasks", []))
    completed_tasks = sum(1 for task in plan_data.get("tasks", []) if task.get("completed"))
    metadata.setdefault("completedTasks", completed_tasks)
    metadata.setdefault("totalXP", plan_data.get("summary", {}).get("totalXP", 0))
    if total_tasks:
        metadata.setdefault("progress", round((completed_tasks / total_tasks) * 100))
    else:
        metadata.setdefault("progress", 0)

    return StudyPlanResponse(
        id=record["id"],
        planId=record["id"],
        userId=record.get("user_id"),
        analysisId=record["analysis_id"],
        status=record.get("status", "active"),
        createdAt=record.get("created_at"),
        updatedAt=record.get("updated_at"),
        startDate=record.get("start_date"),
        endDate=record.get("end_date"),
        totalDays=record.get("total_days"),
        hoursPerDay=record.get("hours_per_day"),
        studyDays=record.get("study_days") or [],
        metadata=metadata,
        planData=plan_data,
    )


@router.post("/study-plan/generate", response_model=StudyPlanResponse)
async def generate_study_plan(request: StudyPlanRequest) -> StudyPlanResponse:
    supabase = get_supabase_client()

    analysis_result = (
        supabase.table("skill_analyses")
        .select("*")
        .eq("id", request.analysis_id)
        .limit(1)
        .execute()
    )

    if not analysis_result.data:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis_row = analysis_result.data[0]
    context = _build_analysis_context(analysis_row)

    plan = _call_openai_for_plan(
        context=context,
        hours_per_day=request.hours_per_day,
        timeline=request.timeline,
        study_days=request.study_days,
    )

    if not plan:
        plan = _generate_mock_plan(
            context=context,
            hours_per_day=request.hours_per_day,
            timeline=request.timeline,
        )

    plan = _normalise_plan(plan, request.hours_per_day, request.timeline)

    plan_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    start_date = created_at.date()
    end_date = start_date + timedelta(days=request.timeline - 1)

    metadata = {
        "progress": 0,
        "totalXP": plan["summary"].get("totalXP", 0),
        "completedTasks": 0,
    }

    record = {
        "id": plan_id,
        "user_id": context.get("user_id"),
        "analysis_id": request.analysis_id,
        "status": "active",
        "created_at": created_at.isoformat(),
        "updated_at": created_at.isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_days": request.timeline,
        "hours_per_day": request.hours_per_day,
        "study_days": request.study_days,
        "plan_data": plan,
        "metadata": metadata,
    }

    try:
        supabase.table("study_plans").insert(record).execute()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[StudyPlan] Failed to store plan in Supabase: {exc}")

    return _format_study_plan_response(record)


@router.get("/study-plan/{plan_id}", response_model=StudyPlanResponse)
async def get_study_plan(plan_id: str) -> StudyPlanResponse:
    supabase = get_supabase_client()
    result = (
        supabase.table("study_plans")
        .select("*")
        .eq("id", plan_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Study plan not found")

    return _format_study_plan_response(result.data[0])


@router.patch("/study-plan/{plan_id}/tasks/{task_index}/complete", response_model=StudyPlanResponse)
async def update_task_completion(plan_id: str, task_index: int, completed: bool) -> StudyPlanResponse:
    supabase = get_supabase_client()
    result = (
        supabase.table("study_plans")
        .select("*")
        .eq("id", plan_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Study plan not found")

    record = result.data[0]
    plan_data = record.get("plan_data") or {}
    tasks = plan_data.get("tasks") or []

    if task_index < 0 or task_index >= len(tasks):
        raise HTTPException(status_code=400, detail="Task index out of range")

    tasks[task_index]["completed"] = completed

    completed_count = sum(1 for task in tasks if task.get("completed"))
    total_tasks = len(tasks)
    progress = round((completed_count / total_tasks) * 100) if total_tasks else 0
    total_xp = sum(task.get("xp", 0) for task in tasks)

    metadata = record.get("metadata") or {}
    metadata.update(
        {
            "completedTasks": completed_count,
            "totalXP": total_xp,
            "progress": progress,
        }
    )

    updated_at = datetime.utcnow().isoformat()

    update_payload = {
        "plan_data": plan_data,
        "metadata": metadata,
        "updated_at": updated_at,
    }

    supabase.table("study_plans").update(update_payload).eq("id", plan_id).execute()

    record.update(update_payload)
    record["updated_at"] = updated_at

    return _format_study_plan_response(record)

