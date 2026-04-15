import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from jobs.models import Job
from django.contrib.auth import get_user_model

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = "Seed database with sample jobs"

    def handle(self, *args, **kwargs):
        recruiter = User.objects.filter(is_superuser=True).first()
        if not recruiter:
            self.stdout.write(self.style.ERROR("No superuser found. Create one first."))
            return

        work_modes = ['remote', 'onsite', 'hybrid']
        job_types = ['full_time', 'part_time', 'internship', 'contract']
        experience_levels = ['fresher', 'junior', 'mid', 'senior']
        currencies = ['INR', 'USD', 'EUR']
        base_title = "Software Development Engineer Intern"
        base_company = "Google"
        base_location = "Mountain View, CA"
        base_skills = "Python, Django, React, SQL"

        for i in range(10):
            Job.objects.create(
                title=f"{base_title} Level {i+1}",
                company_name=base_company,
                description=fake.paragraph(nb_sentences=5),
                responsibilities=fake.paragraph(nb_sentences=3),
                requirements=fake.paragraph(nb_sentences=3),
                location=base_location,
                work_mode=random.choice(work_modes),
                job_type=random.choice(job_types),
                experience_level=random.choice(experience_levels),
                currency=random.choice(currencies),
                salary_min=random.randint(30000, 50000),
                salary_max=random.randint(50001, 100000),
                skills_required=base_skills,
                application_deadline=timezone.now().date() + timezone.timedelta(days=30),
                recruiter=recruiter,
                is_active=True
            )

        self.stdout.write(self.style.SUCCESS("✅ Inserted 10 similar jobs."))

        for i in range(10):
            Job.objects.create(
                title=fake.job(),
                company_name=fake.company(),
                description=fake.paragraph(nb_sentences=5),
                responsibilities=fake.paragraph(nb_sentences=3),
                requirements=fake.paragraph(nb_sentences=3),
                location=fake.city(),
                work_mode=random.choice(work_modes),
                job_type=random.choice(job_types),
                experience_level=random.choice(experience_levels),
                currency=random.choice(currencies),
                salary_min=random.randint(20000, 60000),
                salary_max=random.randint(60001, 120000),
                skills_required=", ".join(fake.words(nb=5, unique=True)),
                application_deadline=timezone.now().date() + timezone.timedelta(days=random.randint(15, 60)),
                recruiter=recruiter,
                is_active=True
            )

        self.stdout.write(self.style.SUCCESS("✅ Inserted 10 different jobs."))