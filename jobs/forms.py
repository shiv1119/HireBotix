# jobs/forms.py
from django import forms
from .models import Job, JOB_TYPE_CHOICES, WORK_MODE_CHOICES, EXPERIENCE_LEVEL, CURRENCY_CHOICES

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'location', 
            'description', 'responsibilities', 'requirements',
            'work_mode', 'job_type', 'experience_level',
            'currency', 'salary_min', 'salary_max', 
            'skills_required', 'application_deadline'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., Senior Software Engineer'
            }),
            'location': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'e.g., New York, NY or Remote'
            }),
            'description': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none',
                'placeholder': 'Describe the role and your company...'
            }),
            'responsibilities': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none',
                'placeholder': 'List the day-to-day responsibilities...'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none',
                'placeholder': 'List required skills, experience, education...'
            }),
            'work_mode': forms.Select(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
            'job_type': forms.Select(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
            'experience_level': forms.Select(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
            'currency': forms.Select(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
            'salary_min': forms.NumberInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'Minimum salary'
            }),
            'salary_max': forms.NumberInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'Maximum salary'
            }),
            'skills_required': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'Python, Django, JavaScript, React'
            }),
            'application_deadline': forms.DateInput(attrs={
                'type': 'date',
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError("Minimum salary cannot be greater than maximum salary.")
        
        return cleaned_data