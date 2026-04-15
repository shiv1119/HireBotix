from django import forms
from .models import (
    Resume, Education, Experience, Skill, AwardAchievement,
    ProfessionalSummary, Link, Certification, Project, JobApplication
)

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'accept': '.pdf,.doc,.docx'
            })
        }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['degree', 'institution', 'start_year', 'end_year', 'grade', 'description']
        widgets = {
            'degree': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., Bachelor of Science in Computer Science'
            }),
            'institution': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., University Name'
            }),
            'start_year': forms.NumberInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'YYYY'
            }),
            'end_year': forms.NumberInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'YYYY (leave blank if current)'
            }),
            'grade': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., 3.8 GPA or First Class'
            }),
            'description': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none',
                'rows': 4,
                'placeholder': 'Describe your achievements, coursework, etc.'
            })
        }

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['job_title', 'company', 'start_date', 'end_date', 'description']
        widgets = {
            'job_title': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., Software Engineer'
            }),
            'company': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., Company Name'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none',
                'rows': 4,
                'placeholder': 'Describe your responsibilities and achievements'
            })
        }

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., Python, Django, React'
            })
        }

class AwardAchievementForm(forms.ModelForm):
    class Meta:
        model = AwardAchievement
        fields = ['title', 'description', 'date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., Employee of the Month'
            }),
            'description': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none',
                'rows': 3,
                'placeholder': 'Describe the award or achievement'
            }),
            'date': forms.DateInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'type': 'date'
            })
        }

class ProfessionalSummaryForm(forms.ModelForm):
    class Meta:
        model = ProfessionalSummary
        fields = ['summary']
        widgets = {
            'summary': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-32 resize-none',
                'rows': 6,
                'placeholder': 'Write a brief professional summary about yourself...'
            })
        }

class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['name', 'url']
        widgets = {
            'name': forms.Select(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }, choices=[
                ('', 'Select platform'),
                ('GitHub', 'GitHub'),
                ('LinkedIn', 'LinkedIn'),
                ('Codeforces', 'Codeforces'),
                ('Portfolio', 'Portfolio Website'),
                ('Other', 'Other')
            ]),
            'url': forms.URLInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'https://...'
            })
        }

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name', 'organization', 'date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., AWS Certified Solutions Architect'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., Amazon Web Services'
            }),
            'date': forms.DateInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'type': 'date'
            })
        }

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'live_link', 'github_link']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'Project Title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none',
                'rows': 4,
                'placeholder': 'Describe your project, technologies used, challenges, etc.'
            }),
            'live_link': forms.URLInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'https://live-demo.com'
            }),
            'github_link': forms.URLInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'https://github.com/username/project'
            })
        }

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['resume']  # Keep the field but we'll customize rendering
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Set queryset but we'll render manually
            self.fields['resume'].queryset = Resume.objects.filter(user=user).order_by('-uploaded_at')
            self.fields['resume'].empty_label = None
            # Make resume field optional in the form since we're handling it manually
            self.fields['resume'].required = False
            
        self.job = job
    
    def clean(self):
        """Custom validation to ensure resume is selected"""
        cleaned_data = super().clean()
        # Don't add validation here since we handle it in the view
        return cleaned_data