from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.enums.jobs import JobTypeEnum, WorkModeEnum

class JobCreate(BaseModel):

    title: str = Field(..., min_length=3, max_length=120)
    company_name: str = Field(..., min_length=2, max_length=120)
    location: Optional[str]
    city: Optional[str]
    country: Optional[str]
    description: str = Field(..., min_length=20)
    requirements: Optional[str]
    responsibilities: Optional[str]
    benefits: Optional[str]
    skills_required: Optional[List[str]]
    languages_required: Optional[List[str]]
    job_type: Optional[str]
    work_mode: Optional[str]
    experience_level: Optional[str]
    min_experience: Optional[int] = Field(None, ge=0, le=40)
    max_experience: Optional[int] = Field(None, ge=0, le=40)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    openings: Optional[int] = Field(None, ge=1)
    apply_link: Optional[HttpUrl]
    contact_email: Optional[EmailStr]
    application_deadline: Optional[datetime]
    is_remote_allowed: Optional[bool]

class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=120)
    company_name: Optional[str] = Field(None, min_length=2, max_length=120)
    location: Optional[str]
    city: Optional[str]
    country: Optional[str]
    description: Optional[str] = Field(None, min_length=20)
    requirements: Optional[str]
    responsibilities: Optional[str]
    benefits: Optional[str]
    skills_required: Optional[List[str]]
    languages_required: Optional[List[str]]
    job_type: Optional[JobTypeEnum]
    work_mode: Optional[WorkModeEnum]
    experience_level: Optional[str]
    min_experience: Optional[int] = Field(None, ge=0, le=40)
    max_experience: Optional[int] = Field(None, ge=0, le=40)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    openings: Optional[int] = Field(None, ge=1)
    apply_link: Optional[HttpUrl]
    contact_email: Optional[EmailStr]
    application_deadline: Optional[datetime]
    is_active: Optional[bool]
    is_remote_allowed: Optional[bool]


class JobResponse(BaseModel):
    id: UUID
    title: str
    company_name: str
    location: Optional[str]
    city: Optional[str]
    country: Optional[str]
    description: str
    requirements: Optional[str]
    responsibilities: Optional[str]
    benefits: Optional[str]
    skills_required: Optional[List[str]]
    languages_required: Optional[List[str]]
    job_type: Optional[str]
    work_mode: Optional[str]
    experience_level: Optional[str]
    min_experience: Optional[int]
    max_experience: Optional[int]
    salary_min: Optional[int]
    salary_max: Optional[int]
    currency: Optional[str]
    openings: Optional[int]
    apply_link: Optional[str]
    contact_email: Optional[str]
    application_deadline: Optional[datetime]
    is_active: bool
    is_remote_allowed: bool
    hr_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True