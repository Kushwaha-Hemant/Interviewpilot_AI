"""String enums shared by models and API schemas.

Stored as plain VARCHAR rather than native PG enums so adding a mode never needs a
migration that rewrites a type.
"""

from __future__ import annotations

from enum import StrEnum


class InterviewMode(StrEnum):
    HR = "hr"
    TECHNICAL = "technical"
    CODING = "coding"
    SYSTEM_DESIGN = "system_design"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class InterviewStatus(StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class TurnKind(StrEnum):
    QUESTION = "question"
    FOLLOW_UP = "follow_up"
    HINT = "hint"


class ParseStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


# Feature 13 — company interview styles. Values feed the prompt builder.
COMPANY_STYLES: dict[str, str] = {
    "google": (
        "Google: heavy emphasis on algorithmic rigor, data structures, and complexity "
        "analysis. Probe for edge cases and ask the candidate to justify trade-offs. "
        "Googleyness questions favour collaboration and ambiguity tolerance."
    ),
    "amazon": (
        "Amazon: anchor behavioural questions on the Leadership Principles (Customer "
        "Obsession, Ownership, Dive Deep, Bias for Action). Demand STAR-structured answers "
        "with concrete metrics. Technical rounds favour scalable, pragmatic designs."
    ),
    "microsoft": (
        "Microsoft: balanced problem-solving and collaboration. Ask the candidate to think "
        "aloud, and follow up on design choices and testing strategy rather than raw speed."
    ),
    "meta": (
        "Meta: fast-paced, high signal density. Expect optimal solutions quickly, then push "
        "on scale and product sense. Behavioural rounds probe impact and moving fast."
    ),
    "netflix": (
        "Netflix: senior-level bar, culture of freedom and responsibility. Probe judgement, "
        "self-direction, and candour. Expect the candidate to defend opinions with evidence."
    ),
    "apple": (
        "Apple: deep domain expertise and craftsmanship. Drill into details of past work, "
        "quality bars, and how the candidate handles secrecy and cross-team dependencies."
    ),
    "tcs": (
        "TCS: fundamentals-first. Cover core language concepts, OOP, DBMS, and SDLC process "
        "questions, plus willingness to relocate and learn new stacks."
    ),
    "infosys": (
        "Infosys: structured assessment of fundamentals, aptitude-style reasoning, and "
        "communication clarity. Favour textbook-correct definitions followed by an example."
    ),
    "accenture": (
        "Accenture: client-facing consulting slant. Blend technical fundamentals with "
        "stakeholder-communication scenarios and delivery-under-pressure situations."
    ),
    "generic": (
        "A well-run, neutral industry interview: fair difficulty ramp, one follow-up per "
        "strong answer, and a hint before moving on when the candidate stalls."
    ),
}
