# applications/admin.py
from django.contrib import admin
from .models import (
    Resume, Education, Experience, Skill,
    ProfessionalSummary, Link, Certification, Project, JobApplication
)

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'file', 'uploaded_at')
    search_fields = ('user__username', 'file')
    list_filter = ('uploaded_at',)

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('user', 'degree', 'institution', 'start_year', 'end_year')
    search_fields = ('user__username', 'degree', 'institution')
    list_filter = ('start_year', 'end_year')

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title', 'company', 'start_date', 'end_date')
    search_fields = ('user__username', 'job_title', 'company')
    list_filter = ('start_date', 'end_date')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'name')
    search_fields = ('user__username', 'name')

@admin.register(ProfessionalSummary)
class ProfessionalSummaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'summary')
    search_fields = ('user__username', 'summary')


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'url')
    search_fields = ('user__username', 'name', 'url')

@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'organization', 'date')
    search_fields = ('user__username', 'name', 'organization')
    list_filter = ('date',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'live_link', 'github_link')
    search_fields = ('user__username', 'title')
    list_filter = ('created_at',)

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'created_at')
    search_fields = ('user__username', 'job__title', 'status')
    list_filter = ('status', 'created_at')

# utils/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import GitHubStats, GitHubContribution

admin.site.register(GitHubContribution)
admin.site.register(GitHubStats)