"""Deterministic offline provider — the whole app runs end-to-end without an API key.

It is NOT a stub that returns empty objects: it produces schema-valid, plausible payloads
derived from a hash of the prompt, so the UI, DB writes, charts and PDF all exercise real
shapes. Set OPENAI_API_KEY (and AI_PROVIDER=auto|openai) to switch to real GPT.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from collections.abc import AsyncIterator

from app.ai.provider import AIProvider, AIProviderError, TModel
from app.schemas.coaching import (
    CoachReport,
    DashboardInsight,
    LearningStep,
    Mistake,
    Recommendation,
    SkillScore,
)
from app.schemas.evaluation import AnswerEvaluation, GeneratedQuestion, InterviewerDecision
from app.schemas.extraction import (
    Education,
    Experience,
    JobProfile,
    Project,
    RequiredSkill,
    ResumeProfile,
    Skill,
)

QUESTION_BANK: dict[str, list[str]] = {
    "hr": [
        "Tell me about yourself and what drew you to this role.",
        "Describe a time you disagreed with a teammate. How did you resolve it?",
        "Tell me about a project where you had to lead without formal authority.",
        "What is the most significant piece of feedback you have received, and what changed?",
        "Where do you see the hardest part of this role being for you?",
    ],
    "technical": [
        "Explain dependency injection and why a framework would provide it.",
        "How does a hash map achieve average O(1) lookup, and when does it degrade?",
        "Walk me through what happens between a client request and a database write in your stack.",
        "How would you make an endpoint idempotent, and why does that matter?",
        "Explain the difference between optimistic and pessimistic locking with an example.",
    ],
    "coding": [
        "Given an array of integers, return the length of the longest subarray whose sum "
        "equals k. Walk me through your approach before coding.",
        "Implement an LRU cache with O(1) get and put. Explain your data-structure choice.",
        "Given a list of intervals, merge all overlapping ones. What is the complexity?",
        "Find the k-th largest element in an unsorted array without fully sorting it.",
    ],
    "system_design": [
        "Design a URL shortener that handles 10k writes and 1M reads per second.",
        "Design the core of a video streaming service like Netflix. Start with the read path.",
        "Design WhatsApp's one-to-one messaging with delivery receipts and offline support.",
        "Design a rate limiter that works across a fleet of stateless API servers.",
    ],
}

FOLLOW_UPS = [
    "You mentioned that at a high level — can you compare it against the alternative and "
    "say when you would pick each?",
    "Good. What breaks first if traffic goes up 100x, and how would you detect it?",
    "Can you make that concrete with an example from something you have actually built?",
    "What is the failure mode of that approach, and how would you test for it?",
]

HINTS = [
    "Take your time. Start by naming the moving parts, then say how they talk to each other.",
    "A hint: think about what happens on the second identical request.",
    "Try walking through a tiny example out loud — three elements is enough.",
]


def _seed(*parts: str) -> int:
    digest = hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _pick(items: list[str], seed: int) -> str:
    return items[seed % len(items)]


def _score(seed: int, low: int = 62, high: int = 95) -> int:
    return low + (seed % (high - low + 1))


def _detect_mode(text: str) -> str:
    lowered = text.lower()
    for mode in ("system_design", "coding", "hr"):
        if mode.replace("_", " ") in lowered or mode in lowered:
            return mode
    return "technical"


def _detect_skills(text: str) -> list[str]:
    known = [
        "Java", "Spring Boot", "React", "Node.js", "Python", "SQL", "Docker", "Kubernetes",
        "AWS", "TypeScript", "PostgreSQL", "Redis", "Microservices", "FastAPI", "Next.js",
    ]
    found = [s for s in known if re.search(re.escape(s), text, re.IGNORECASE)]
    return found or ["Data Structures", "System Design", "Communication"]


class MockProvider(AIProvider):
    name = "mock"

    async def structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[TModel],
        fast: bool = False,
    ) -> TModel:
        await asyncio.sleep(0.05)  # keep async paths honest
        seed = _seed(system, user)
        builder = _BUILDERS.get(schema.__name__)
        if builder is None:
            raise AIProviderError(
                f"MockProvider has no builder for {schema.__name__}. "
                "Add one in app/ai/mock_provider.py or run with a real OPENAI_API_KEY."
            )
        return builder(seed, system, user)  # type: ignore[return-value]

    async def text(self, *, system: str, user: str, fast: bool = False) -> str:
        await asyncio.sleep(0.05)
        return _pick(QUESTION_BANK[_detect_mode(system + user)], _seed(system, user))

    async def stream_text(
        self,
        *,
        system: str,
        user: str,
        fast: bool = False,
    ) -> AsyncIterator[str]:
        full = await self.text(system=system, user=user, fast=fast)
        for token in re.findall(r"\S+\s*", full):
            await asyncio.sleep(0.02)
            yield token

    async def transcribe(self, *, audio: bytes, filename: str) -> str:
        await asyncio.sleep(0.05)
        return (
            "[mock transcript] I would approach this by first clarifying the requirements, "
            "then outlining the data model, and finally discussing trade-offs."
        )

    async def speak(self, *, text: str) -> bytes:
        await asyncio.sleep(0.05)
        # Minimal silent MP3 frame — enough for the client to treat it as audio.
        return b"\xff\xfb\x90\x00" + b"\x00" * 512


# --------------------------------------------------------------------------- builders


def _resume_profile(seed: int, system: str, user: str) -> ResumeProfile:
    skills = _detect_skills(user)
    return ResumeProfile(
        full_name="Candidate Name",
        headline=f"Engineer with hands-on {skills[0]} experience",
        years_of_experience=float(1 + seed % 6),
        skills=[
            Skill(
                name=s,
                category="framework" if s in {"Spring Boot", "React", "FastAPI", "Next.js"} else "language",
                proficiency=["intermediate", "advanced", "expert"][(seed + i) % 3],
            )
            for i, s in enumerate(skills[:8])
        ],
        projects=[
            Project(
                name="Order Management Service",
                description="REST service handling order lifecycle with async fulfilment.",
                technologies=skills[:3],
                impact="Cut p95 latency from 800ms to 180ms",
            )
        ],
        experience=[
            Experience(
                company="Acme Technologies",
                title="Software Engineer",
                duration="2023 - Present",
                highlights=[
                    "Built and owned three production microservices",
                    "Reduced deployment time by 40% with CI improvements",
                ],
                technologies=skills[:4],
            )
        ],
        education=[
            Education(
                institution="University",
                degree="B.Tech",
                field_of_study="Computer Science",
                year="2023",
                score="8.2 CGPA",
            )
        ],
        achievements=["Top performer award", "Open-source contributor"],
        certifications=["AWS Certified Cloud Practitioner"],
        target_roles=["Backend Developer", "Full Stack Developer"],
    )


def _job_profile(seed: int, system: str, user: str) -> JobProfile:
    skills = _detect_skills(user)
    return JobProfile(
        title="Software Engineer",
        company="Hiring Company",
        seniority=["junior", "mid", "senior"][seed % 3],
        min_years_experience=float(seed % 5),
        required_skills=[
            RequiredSkill(name=s, importance="must_have" if i < 3 else "nice_to_have")
            for i, s in enumerate(skills[:6])
        ],
        responsibilities=[
            "Design, build and operate backend services",
            "Collaborate with product and design on requirements",
            "Own quality through tests, monitoring and code review",
        ],
        keywords=skills[:6] + ["REST", "CI/CD", "Agile"],
        domain="generic",
    )


def _generated_question(seed: int, system: str, user: str) -> GeneratedQuestion:
    mode = _detect_mode(system + user)
    skills = _detect_skills(user)
    return GeneratedQuestion(
        question=_pick(QUESTION_BANK[mode], seed),
        skill_tag=skills[seed % len(skills)],
        difficulty=["easy", "medium", "hard"][seed % 3],
        expected_points=[
            "States the core concept correctly",
            "Gives a concrete example from experience",
            "Names at least one trade-off",
        ],
        rationale="Targets a skill claimed on the resume that the JD lists as must-have.",
    )


def _answer_evaluation(seed: int, system: str, user: str) -> AnswerEvaluation:
    answer = user.lower()
    # Reward substance so the mock still produces a believable score spread.
    length_bonus = min(len(answer) // 120, 12)
    base = _score(seed, 55, 82) + length_bonus
    technical = min(base, 98)
    return AnswerEvaluation(
        technical_score=technical,
        communication=min(technical + (seed % 7) - 3, 99),
        confidence=min(technical + (seed % 5) - 2, 99),
        grammar=min(technical + 6, 99),
        clarity=min(technical + (seed % 4), 99),
        overall=technical,
        feedback=(
            "Solid structure and you covered the main idea. "
            "Tighten it by naming a concrete trade-off and an example from your own work."
        ),
        covered_points=["States the core concept correctly"],
        missed_points=["Names at least one trade-off"] if technical < 85 else [],
        red_flags=[],
    )


def _interviewer_decision(seed: int, system: str, user: str) -> InterviewerDecision:
    lowered = user.lower()
    # Very short or empty answers get a hint, like a real interviewer would give.
    answer_len = len(lowered)
    if answer_len < 60 or "i don't know" in lowered or "not sure" in lowered:
        return InterviewerDecision(
            action="hint",
            reason="Candidate stalled or gave a very thin answer.",
            message=_pick(HINTS, seed),
            skill_tag=_detect_skills(user)[0],
        )
    if seed % 3 != 0:
        return InterviewerDecision(
            action="follow_up",
            reason="Answer was decent but stayed at the surface.",
            message=_pick(FOLLOW_UPS, seed),
            skill_tag=_detect_skills(user)[0],
        )
    return InterviewerDecision(
        action="next",
        reason="Topic sufficiently covered; move on for breadth.",
        message="",
        skill_tag="",
    )


def _coach_report(seed: int, system: str, user: str) -> CoachReport:
    skills = _detect_skills(user)
    weak = skills[-2:] if len(skills) > 2 else ["Docker", "AWS"]
    return CoachReport(
        summary=(
            "The candidate communicates clearly and has real hands-on experience with the "
            "core stack. Answers were structured but often stopped short of trade-offs and "
            "production concerns. Depth on infrastructure and scaling is the main gap. "
            "With focused practice they would interview well for a mid-level backend role."
        ),
        strengths=[
            f"Fluent with {skills[0]} fundamentals",
            "Clear, well-paced communication",
            "Gives concrete examples from past projects",
        ],
        weaknesses=[f"Shallow depth on {w}" for w in weak]
        + ["Rarely volunteers trade-offs unprompted"],
        mistakes=[
            Mistake(
                topic=weak[0],
                what_went_wrong="Described the happy path only, without failure handling.",
                correct_answer=(
                    "A strong answer names the failure modes, how they are detected, and the "
                    "fallback behaviour."
                ),
            )
        ],
        recommendations=[
            Recommendation(
                topic=w,
                why=f"{w} appears in the target job description as a must-have.",
                resources=[f"Official {w} documentation", f"Build a small project using {w}"],
            )
            for w in weak
        ],
        learning_plan=[
            LearningStep(
                week=1,
                focus=weak[0],
                tasks=[f"Complete the {weak[0]} fundamentals track", "Write notes on failure modes"],
                mini_project=f"Containerise an existing service with {weak[0]}",
            ),
            LearningStep(
                week=2,
                focus=weak[-1],
                tasks=["Study three real architectures", "Re-answer this interview's weakest question"],
                mini_project="Deploy the service with health checks and metrics",
            ),
            LearningStep(
                week=3,
                focus="Mock interview repetition",
                tasks=["Run three timed mock interviews", "Review every follow-up you missed"],
                mini_project="",
            ),
        ],
        skill_breakdown=[
            SkillScore(skill=s, score=_score(_seed(s, str(seed)), 55, 94)) for s in skills[:6]
        ],
        readiness_percent=_score(seed, 60, 88),
        readiness_role="Backend Developer",
        estimated_prep_time="3 weeks",
    )


def _dashboard_insight(seed: int, system: str, user: str) -> DashboardInsight:
    skills = _detect_skills(user)
    focus = skills[seed % len(skills)]
    return DashboardInsight(
        recommendation=(
            f"Run a technical mock focused on {focus} this week and force yourself to name "
            "a trade-off in every answer."
        ),
        focus_skill=focus,
        reason=f"{focus} scored lowest across your recent interviews.",
    )


_BUILDERS = {
    "ResumeProfile": _resume_profile,
    "JobProfile": _job_profile,
    "GeneratedQuestion": _generated_question,
    "AnswerEvaluation": _answer_evaluation,
    "InterviewerDecision": _interviewer_decision,
    "CoachReport": _coach_report,
    "DashboardInsight": _dashboard_insight,
}
