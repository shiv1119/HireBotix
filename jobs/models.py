from django.db import models
from django.contrib.auth.models import User

JOB_TYPE_CHOICES = [
    ('full_time', 'Full Time'),
    ('part_time', 'Part Time'),
    ('internship', 'Internship'),
    ('contract', 'Contract'),
]

EXPERIENCE_LEVEL = [
    ('fresher', 'Fresher'),
    ('junior', 'Junior'),
    ('mid', 'Mid-Level'),
    ('senior', 'Senior'),
]

WORK_MODE_CHOICES = [
    ('onsite', 'Onsite'),
    ('remote', 'Remote'),
    ('hybrid', 'Hybrid'),
]

CURRENCY_CHOICES = [
    ('INR', '₹ INR'),
    ('USD', '$ USD'),
    ('EUR', '€ EUR'),
]

class Job(models.Model):
    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posted_jobs"
    )

    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)

    description = models.TextField()
    responsibilities = models.TextField()
    requirements = models.TextField()

    location = models.CharField(max_length=255)
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES)

    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL)

    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='INR')

    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)

    skills_required = models.TextField(help_text="Comma separated skills")

    is_active = models.BooleanField(default=True)
    application_deadline = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_currency_symbol(self):
        return {
            'INR': '₹',
            'USD': '$',
            'EUR': '€',
        }.get(self.currency, '')

    def __str__(self):
        return f"{self.title} at {self.company_name}"