"""Pydantic models used as OpenAI Structured Output schemas.

Every field here is REQUIRED on purpose: OpenAI strict structured outputs reject optional
fields, so "unknown" is expressed as an empty string / empty list rather than null.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- resume


class Skill(BaseModel):
    name: str
    category: str = Field(description="e.g. language, framework, database, cloud, tool, soft")
    proficiency: str = Field(description="one of: beginner, intermediate, advanced, expert")


class Project(BaseModel):
    name: str
    description: str
    technologies: list[str]
    impact: str = Field(description="Measurable outcome, or empty string if none stated")


class Experience(BaseModel):
    company: str
    title: str
    duration: str
    highlights: list[str]
    technologies: list[str]


class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    year: str
    score: str = Field(description="CGPA/percentage as written, or empty string")


class ResumeProfile(BaseModel):
    """Feature 3 — structured resume extraction."""

    full_name: str
    headline: str = Field(description="One-line professional summary")
    years_of_experience: float
    skills: list[Skill]
    projects: list[Project]
    experience: list[Experience]
    education: list[Education]
    achievements: list[str]
    certifications: list[str]
    target_roles: list[str] = Field(description="Roles this profile is a plausible fit for")


# ------------------------------------------------------------------------------ job


class RequiredSkill(BaseModel):
    name: str
    importance: str = Field(description="one of: must_have, nice_to_have")


class JobProfile(BaseModel):
    """Feature 4 — structured job-description extraction."""

    title: str
    company: str
    seniority: str = Field(description="e.g. intern, junior, mid, senior, staff")
    min_years_experience: float
    required_skills: list[RequiredSkill]
    responsibilities: list[str]
    keywords: list[str]
    domain: str = Field(description="e.g. fintech, e-commerce, healthcare, generic")
