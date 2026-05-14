from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import secrets

class Company(models.Model):
    VERIFICATION_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    registration_number = models.CharField(max_length=100, unique=True, help_text="GST/Company Registration Number")
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)
    
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20)
    
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_companies')
    rejection_reason = models.TextField(blank=True, null=True)
    
    registration_document = models.FileField(upload_to='company_documents/registration/', blank=True, null=True)
    tax_document = models.FileField(upload_to='company_documents/tax/', blank=True, null=True)
    
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_verification_status_display()})"
    
    def is_verified(self):
        return self.verification_status == 'verified'
    
    def can_post_jobs(self):
        return self.is_verified()
    
    def get_active_jobs_count(self):
        return self.jobs.filter(is_active=True, is_approved=True).count()


class EmployeeRole(models.Model):
    ROLE_TYPES = [
        ('company_admin', 'Company Admin'),
        ('recruiter', 'Recruiter'),
        ('hr_manager', 'HR Manager'),
        ('hiring_manager', 'Hiring Manager'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=50, choices=ROLE_TYPES)
    can_post_jobs = models.BooleanField(default=False)
    can_edit_jobs = models.BooleanField(default=False)
    can_view_applications = models.BooleanField(default=True)
    can_manage_team = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.company.name} - {self.get_name_display()}"


class CompanyEmployee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employments')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    role = models.ForeignKey(EmployeeRole, on_delete=models.PROTECT, related_name='employees')
    
    employee_id = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'company']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name} at {self.company.name}"
    
    def can_post_jobs(self):
        return self.role.can_post_jobs and self.is_active and self.company.can_post_jobs()
    
    def can_view_applications(self):
        return self.role.can_view_applications and self.is_active


class CompanyInvitation(models.Model):
    INVITATION_STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(CompanyEmployee, on_delete=models.CASCADE, related_name='sent_invitations')
    invited_email = models.EmailField()
    role = models.ForeignKey(EmployeeRole, on_delete=models.PROTECT)
    
    token = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=INVITATION_STATUS, default='pending')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Invitation to {self.invited_email} for {self.company.name}"
    
    def is_valid(self):
        return self.status == 'pending' and self.expires_at > timezone.now()