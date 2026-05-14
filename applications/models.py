from django.db import models
from django.contrib.auth.models import User
from jobs.models import Job

WORK_MODE_CHOICES = [
    ('full_time', 'Full Time'),
    ('part_time', 'Part Time'),
    ('internship', 'Internship'),
    ('contract', 'Contract'),
]

class Education(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='educations')
    degree = models.CharField(max_length=255)
    institution = models.CharField(max_length=255)
    start_year = models.IntegerField()
    end_year = models.IntegerField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Experience(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiences')
    job_title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Skill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ProfessionalSummary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='summary')
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Link(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='links')
    name = models.CharField(max_length=100)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Certification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    description = models.TextField()
    live_link = models.URLField(blank=True, null=True)
    github_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

APPLICATION_STATUS = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('reviewed', 'Reviewed'),
    ('shortlisted', 'Shortlisted'),
    ('interviewed', 'Interviewed'),
    ('offered', 'Offered'),
    ('hired', 'Hired'),
    ('rejected', 'Rejected'),
]

ATS_ANALYSIS_STATUS = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='resumes/')
    is_default = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class JobApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='draft')
    
    cover_letter = models.TextField(blank=True)
    
    # ATS Integration
    ats_score = models.ForeignKey('ats_checker.ATSScore', on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    ats_analysis_status = models.CharField(max_length=20, choices=ATS_ANALYSIS_STATUS, default='pending')
    ats_analysis_started_at = models.DateTimeField(null=True, blank=True)
    ats_analysis_completed_at = models.DateTimeField(null=True, blank=True)
    is_github_skills_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'job']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.job.title}"
    
    def submit(self):
        """Submit the application"""
        if self.status == 'draft':
            self.status = 'submitted'
            self.save()
            return True
        return False
    
    def can_withdraw(self):
        """Check if application can be withdrawn"""
        return self.status in ['submitted', 'reviewed']
    
    def get_status_display_color(self):
        """Get Bootstrap color class for status"""
        colors = {
            'draft': 'secondary',
            'submitted': 'primary',
            'reviewed': 'info',
            'shortlisted': 'success',
            'interviewed': 'warning',
            'offered': 'success',
            'hired': 'success',
            'rejected': 'danger',
        }
        return colors.get(self.status, 'secondary')
    
    def verify_github_skills(self):
        """
        Verify if user's GitHub languages match with their skills
        Returns True if at least 4 skills match, False otherwise
        """
        # Get user's skills
        user_skills = set(self.user.skills.values_list('name', flat=True))
        
        # Get user's GitHub stats
        github_stats = getattr(self.user, 'github_stats', None)
        if not github_stats or not github_stats.languages:
            return False
        
        # Get GitHub languages (keys from languages dict)
        github_languages = set(github_stats.languages.keys())
        
        # Find matching skills (case-insensitive)
        matching_skills = set()
        user_skills_lower = {skill.lower() for skill in user_skills}
        
        for github_lang in github_languages:
            if github_lang.lower() in user_skills_lower:
                matching_skills.add(github_lang)
        
        # Also check partial matches (e.g., "JavaScript" vs "Javascript")
        for user_skill in user_skills:
            for github_lang in github_languages:
                if user_skill.lower() in github_lang.lower() or github_lang.lower() in user_skill.lower():
                    matching_skills.add(github_lang)
        
        # Return True if at least 4 skills match
        return len(matching_skills) >= 4
    
    def update_github_skills_verification(self):
        """Update the is_github_skills_verified field"""
        self.is_github_skills_verified = self.verify_github_skills()
        self.save(update_fields=['is_github_skills_verified'])
        return self.is_github_skills_verified


class ApplicationNote(models.Model):
    """Notes added by recruiters on applications"""
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='notes')
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='application_notes')
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Note for {self.application}"


class ApplicationActivity(models.Model):
    """Track application activity/log"""
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=100)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='application_activities')
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.action} - {self.application} at {self.created_at}"


from django.utils import timezone
from django.utils import timezone

class GitHubStats(models.Model):
    """Store GitHub user statistics - Only essential fields"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='github_stats')
    username = models.CharField(max_length=255)
    github_url = models.URLField()
    
    # Core Statistics
    public_repos = models.IntegerField(default=0)
    total_stars = models.IntegerField(default=0)
    total_forks = models.IntegerField(default=0)
    
    # Contributions
    total_commits = models.IntegerField(default=0)
    total_pull_requests = models.IntegerField(default=0)
    total_issues = models.IntegerField(default=0)
    
    # Languages Used (Store as JSON with percentages: {"Python": 45.5, "JavaScript": 30.2})
    languages = models.JSONField(default=dict, blank=True)
    
    # Metadata
    last_fetched = models.DateTimeField(null=True, blank=True)
    fetch_status = models.CharField(max_length=20, default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "GitHub Stats"
        ordering = ['-last_fetched']
    
    def __str__(self):
        return f"{self.username} - Repos: {self.public_repos}, Stars: {self.total_stars}"
    
    def get_top_languages(self, limit=5):
        """Get top N languages by percentage"""
        if not self.languages:
            return []
        sorted_langs = sorted(self.languages.items(), key=lambda x: x[1], reverse=True)
        return [{'name': lang, 'percentage': percent} for lang, percent in sorted_langs[:limit]]
    
    def is_data_fresh(self, hours=24):
        """Check if data is fresh (less than X hours old)"""
        if not self.last_fetched:
            return False
        return (timezone.now() - self.last_fetched).total_seconds() < (hours * 3600)
    
    @property
    def total_contributions(self):
        """Total contributions count"""
        return self.total_commits + self.total_pull_requests + self.total_issues


class GitHubContribution(models.Model):
    """Store GitHub contributions over time"""
    github_stats = models.ForeignKey(GitHubStats, on_delete=models.CASCADE, related_name='contributions')
    date = models.DateField()
    contribution_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['github_stats', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.github_stats.username} - {self.date}: {self.contribution_count}"