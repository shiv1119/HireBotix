from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from app.models.jobs import JobPosting

async def create_job(db: AsyncSession, job_data: dict, hr_id: UUID):
    job = JobPosting(**job_data, hr_id=hr_id)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

async def get_jobs(db: AsyncSession):
    result = await db.execute(
        select(JobPosting).where(JobPosting.is_active == True)
    )
    return result.scalars().all()


async def get_job_by_id(db: AsyncSession, job_id: UUID):
    result = await db.execute(
        select(JobPosting).where(JobPosting.id == job_id)
    )
    return result.scalar_one_or_none()

async def update_job(db: AsyncSession, job, update_data: dict):
    for field, value in update_data.items():
        setattr(job, field, value)
    await db.commit()
    await db.refresh(job)
    return job

async def delete_job(db: AsyncSession, job):
    job.is_active = False
    await db.commit()
    return {"message": "Job deleted successfully"}