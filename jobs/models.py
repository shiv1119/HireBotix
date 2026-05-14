from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Import company models - handle import gracefully if company app doesn't exist yet
try:
    from company.models import Company, CompanyEmployee
except ImportError:
    Company = None
    CompanyEmployee = None

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
    # Company relationship fields
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name="jobs", 
        null=True, 
        blank=True
    )
    posted_by = models.ForeignKey(
        CompanyEmployee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="posted_jobs"
    )
    
    # Approval workflow fields
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_jobs'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Job details
    title = models.CharField(max_length=255)
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
    target_ats = models.IntegerField(
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum ATS score required for shortlisting (0-100)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def get_currency_symbol(self):
        return {
            'INR': '₹',
            'USD': '$',
            'EUR': '€',
        }.get(self.currency, '')
    
    def is_published(self):
        """Check if job is published and visible to applicants"""
        if self.company:
            return self.company.is_verified() and self.is_approved and self.is_active
        return self.is_active
    
    def can_be_edited_by(self, user):
        """Check if user can edit this job"""
        if user.is_staff:
            return True
        
        # Check company employee permission
        if self.company and hasattr(user, 'employments'):
            employee = user.employments.filter(company=self.company, is_active=True).first()
            if employee and employee.role.can_edit_jobs:
                return True
        
        return False
    
    def is_application_open(self):
        """Check if job is accepting applications"""
        # Check if job is published
        if not self.is_published():
            return False
        
        # Check deadline
        if self.application_deadline:
            from django.utils import timezone
            if self.application_deadline < timezone.now().date():
                return False
        
        return True

    def __str__(self):
        return f"{self.title} at {self.company.name if self.company else 'Unknown Company'}"