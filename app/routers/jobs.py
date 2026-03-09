from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.dependencies import get_db
from app.schemas.jobs import JobCreate, JobUpdate, JobResponse
from app.services.jobs_service import (
    create_job,
    get_jobs,
    get_job_by_id,
    update_job,
    delete_job
)
from app.models.users import User
from app.models.enums.user import RoleEnum
from app.routers.dependencies import get_current_user
from app.core.exceptions import (
    AuthorizationException,
    NotFoundException
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=JobResponse)
async def create_job_route(
    job: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.HR.value:
        raise AuthorizationException("Only HR can create jobs")

    return await create_job(db, job.model_dump(), current_user.id)

@router.get("/", response_model=list[JobResponse])
async def get_jobs_route(db: AsyncSession = Depends(get_db)):
    return await get_jobs(db)

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_route(job_id: UUID, db: AsyncSession = Depends(get_db)):
    job = await get_job_by_id(db, job_id)
    if not job:
        raise NotFoundException("Job not found")
    return job

@router.put("/{job_id}", response_model=JobResponse)
async def update_job_route(
    job_id: UUID,
    job_data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = await get_job_by_id(db, job_id)
    if not job:
        raise NotFoundException("Job not found")
    if job.hr_id != current_user.id and current_user.role != RoleEnum.HR.value:
        raise AuthorizationException("Not authorized")
    return await update_job(db,job, job_data.model_dump(exclude_unset=True))

@router.delete("/{job_id}")
async def delete_job_route(job_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = await get_job_by_id(db, job_id)
    if not job:
        raise NotFoundException("Job not found")
    if job.hr_id != current_user.id and current_user.role != RoleEnum.HR.value:
        raise AuthorizationException("Not authorized")
    return await delete_job(db, job)