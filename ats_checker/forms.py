# forms.py
from django import forms
from .models import *

class ResumeUploadForm(forms.Form):
    """Form for uploading resume"""
    resume = forms.FileField(
        label='Resume (PDF only)',
        help_text='Maximum file size: 10MB',
        widget=forms.FileInput(attrs={
            'accept': '.pdf',
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )


class JobDescriptionForm(forms.Form):
    """Form for job description"""
    title = forms.CharField(
        label='Job Title',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'e.g., Senior Full Stack Developer'
        })
    )
    company = forms.CharField(
        label='Company',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Company name (optional)'
        })
    )
    jd_text = forms.CharField(
        label='Job Description',
        widget=forms.Textarea(attrs={
            'rows': 8,
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Paste the complete job description here...'
        })
    )
