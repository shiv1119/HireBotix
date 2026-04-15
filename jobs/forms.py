from django import forms
from .models import Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'company_name', 'location', 
            'description', 'responsibilities', 'requirements',
            'work_mode', 'job_type', 'experience_level',
            'currency', 'salary_min', 'salary_max', 
            'skills_required', 'application_deadline'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),

            'location': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
        
            # TEXTAREAS
            'description': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none'
            }),
            'responsibilities': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none'
            }),

            # SELECTS
            'work_mode': forms.Select(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
            'job_type': forms.Select(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
            'experience_level': forms.Select(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),

            # 🔥 NEW FIELD
            'currency': forms.Select(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),

            # SALARY
            'salary_min': forms.NumberInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
            'salary_max': forms.NumberInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),

            'skills_required': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),

            'application_deadline': forms.DateInput(attrs={
                'type': 'date',
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
        }