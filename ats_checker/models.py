# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class ExtractedResumeContent(models.Model):
    """Store extracted resume content"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    filename = models.CharField(max_length=255)
    raw_text = models.TextField()
    structured_json = models.JSONField(default=dict)
    extraction_method = models.CharField(max_length=20, default='pdfplumber')
    word_count = models.IntegerField(default=0)
    page_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Extracted Resume Contents"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class JobDescription(models.Model):
    """Store job descriptions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    raw_text = models.TextField()
    formatted_jd = models.TextField()
    structured_json = models.JSONField(default=dict)
    word_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Job Descriptions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class ATSScore(models.Model):
    """Store ATS scores and comprehensive analysis"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    resume = models.ForeignKey(ExtractedResumeContent, on_delete=models.CASCADE)
    job_description = models.ForeignKey(JobDescription, on_delete=models.CASCADE)
    
    # Overall scores
    overall_score = models.FloatField()  # 0-100
    match_percentage = models.FloatField()
    
    # Detailed scores
    skills_match_score = models.FloatField()
    experience_match_score = models.FloatField()
    education_match_score = models.FloatField()
    keyword_match_score = models.FloatField()
    formatting_score = models.FloatField()
    completeness_score = models.FloatField()
    
    # Detailed analysis
    matching_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    matching_keywords = models.JSONField(default=list)
    missing_keywords = models.JSONField(default=list)
    matching_experience = models.JSONField(default=list)
    missing_experience = models.JSONField(default=list)
    
    # Section-wise suggestions
    section_suggestions = models.JSONField(default=dict)  # {section: [suggestions]}
    spelling_errors = models.JSONField(default=list)  # [{word: "", suggestion: "", context: ""}]
    
    # Grammar and style issues
    grammar_issues = models.JSONField(default=list)
    style_improvements = models.JSONField(default=list)
    
    # Formatting issues
    formatting_issues = models.JSONField(default=list)
    
    # Recommendations
    recommendations = models.JSONField(default=list)
    detailed_feedback = models.TextField(blank=True)
    
    # Resume strengths and weaknesses
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    
    # Improvement suggestions by category
    improvement_suggestions = models.JSONField(default=dict)  # {category: [suggestions]}
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "ATS Scores"
        ordering = ['-created_at']
        unique_together = ['resume', 'job_description']
    
    def __str__(self):
        return f"{self.resume.filename} vs {self.job_description.title} - Score: {self.overall_score}"