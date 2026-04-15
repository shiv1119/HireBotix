# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ExtractedResumeContent, JobDescription, ATSScore


class ATSScoreInline(admin.TabularInline):
    """Inline view of ATS scores from resume or job description"""
    model = ATSScore
    extra = 0
    fields = ('job_description', 'overall_score', 'match_percentage', 'created_at')
    readonly_fields = ('job_description', 'overall_score', 'match_percentage', 'created_at')
    can_delete = False
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ExtractedResumeContent)
class ExtractedResumeContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'filename', 'user', 'word_count', 'page_count', 'extraction_method', 'created_at')
    list_filter = ('extraction_method', 'created_at', 'updated_at', 'user')
    search_fields = ('filename', 'raw_text', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'word_count', 'page_count')
    inlines = [ATSScoreInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'filename', 'extraction_method')
        }),
        ('Content Statistics', {
            'fields': ('word_count', 'page_count')
        }),
        ('Extracted Data', {
            'fields': ('raw_text', 'structured_json'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def view_resume_link(self, obj):
        """Create a link to view the resume content"""
        if obj.id:
            url = reverse('admin:ats_checker_extractedresumecontent_change', args=[obj.id])
            return format_html('<a href="{}">View Details</a>', url)
        return "-"
    view_resume_link.short_description = 'Actions'


@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'user', 'word_count', 'created_at')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('title', 'company', 'raw_text', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'word_count')
    inlines = [ATSScoreInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'company')
        }),
        ('Content Statistics', {
            'fields': ('word_count',)
        }),
        ('Job Description Content', {
            'fields': ('raw_text', 'formatted_jd', 'structured_json'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ATSScore)
class ATSScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_resume_filename', 'get_job_title', 'user', 'overall_score', 'match_percentage', 'created_at')
    list_filter = ('created_at', 'user', 'overall_score')
    search_fields = (
        'resume__filename', 'job_description__title', 'job_description__company',
        'user__username', 'user__email', 'detailed_feedback'
    )
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'resume', 'job_description')
        }),
        ('Scores', {
            'fields': (
                'overall_score', 'match_percentage',
                'skills_match_score', 'experience_match_score', 
                'education_match_score', 'keyword_match_score',
                'formatting_score', 'completeness_score'
            )
        }),
        ('Skills Analysis', {
            'fields': ('matching_skills', 'missing_skills'),
            'classes': ('collapse',)
        }),
        ('Keyword Analysis', {
            'fields': ('matching_keywords', 'missing_keywords'),
            'classes': ('collapse',)
        }),
        ('Experience Analysis', {
            'fields': ('matching_experience', 'missing_experience'),
            'classes': ('collapse',)
        }),
        ('Strengths & Weaknesses', {
            'fields': ('strengths', 'weaknesses'),
            'classes': ('collapse',)
        }),
        ('Improvement Suggestions', {
            'fields': (
                'section_suggestions', 'improvement_suggestions',
                'recommendations', 'detailed_feedback'
            ),
            'classes': ('collapse',)
        }),
        ('Issues Found', {
            'fields': (
                'spelling_errors', 'grammar_issues', 
                'style_improvements', 'formatting_issues'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'resume', 'job_description')
    
    def get_resume_filename(self, obj):
        """Get resume filename with link"""
        if obj.resume:
            url = reverse('admin:ats_checker_extractedresumecontent_change', args=[obj.resume.id])
            return format_html('<a href="{}">{}</a>', url, obj.resume.filename[:50])
        return "-"
    get_resume_filename.short_description = 'Resume'
    
    def get_job_title(self, obj):
        """Get job title with link"""
        if obj.job_description:
            url = reverse('admin:ats_checker_jobdescription_change', args=[obj.job_description.id])
            return format_html('<a href="{}">{}</a>', url, obj.job_description.title)
        return "-"
    get_job_title.short_description = 'Job Title'
    
    def score_color(self, obj):
        """Color code the score based on value"""
        if obj.overall_score >= 80:
            color = 'green'
        elif obj.overall_score >= 60:
            color = 'orange'
        elif obj.overall_score >= 40:
            color = 'yellow'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.overall_score
        )
    score_color.short_description = 'Score'
    
    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly for viewing only"""
        if obj:  # Editing existing object
            return [field.name for field in self.model._meta.fields if field.name != 'id']
        return self.readonly_fields
    
    def has_add_permission(self, request):
        """Disable adding via admin (should be created programmatically)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow delete for cleanup"""
        return True
    
    actions = ['delete_selected', 'export_as_csv']
    
    def export_as_csv(self, request, queryset):
        """Export selected ATS scores as CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ats_scores_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Resume', 'Job Title', 'User', 'Overall Score', 'Skills Match',
            'Experience Match', 'Education Match', 'Keyword Match', 'Created At'
        ])
        
        for score in queryset:
            writer.writerow([
                score.id,
                score.resume.filename if score.resume else '',
                score.job_description.title if score.job_description else '',
                score.user.username if score.user else '',
                f"{score.overall_score:.1f}%",
                f"{score.skills_match_score:.1f}%",
                f"{score.experience_match_score:.1f}%",
                f"{score.education_match_score:.1f}%",
                f"{score.keyword_match_score:.1f}%",
                score.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_as_csv.short_description = "Export selected scores as CSV"