# company/forms.py
from django import forms
from .models import Company, EmployeeRole, CompanyInvitation

class CompanyRegistrationForm(forms.ModelForm):
    confirm_email = forms.EmailField(
        label='Confirm Email',
        widget=forms.EmailInput(attrs={
            'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
            'placeholder': 'Confirm email address'
        })
    )
    
    class Meta:
        model = Company
        fields = [
            'name', 'registration_number', 'tax_id',
            'email', 'phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code',
            'registration_document', 'tax_document', 'logo', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'Enter company name'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'GST/Company Registration Number'
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'Tax ID (optional)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'company@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': '+91 1234567890'
            }),
            'website': forms.URLInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'https://www.example.com'
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'Street address, P.O. Box'
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'Apartment, suite, unit, etc. (optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'State/Province'
            }),
            'country': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'Country'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'placeholder': 'Postal/ZIP code'
            }),
            'registration_document': forms.FileInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'tax_document': forms.FileInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md',
                'accept': '.jpg,.jpeg,.png'
            }),
            'description': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none',
                'rows': 4,
                'placeholder': 'Describe your company, culture, values, mission, etc.'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirm_email = cleaned_data.get('confirm_email')
        
        if email and confirm_email and email != confirm_email:
            raise forms.ValidationError("Email addresses don't match")
        
        return cleaned_data
    
    def clean_registration_number(self):
        reg_number = self.cleaned_data.get('registration_number')
        if Company.objects.filter(registration_number=reg_number).exists():
            raise forms.ValidationError("A company with this registration number already exists.")
        return reg_number
    
    def clean_registration_document(self):
        doc = self.cleaned_data.get('registration_document')
        if doc:
            # Validate file size (max 5MB)
            if doc.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 5MB.")
        return doc
    
    def clean_tax_document(self):
        doc = self.cleaned_data.get('tax_document')
        if doc:
            # Validate file size (max 5MB)
            if doc.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 5MB.")
        return doc
    
    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            # Validate file size (max 2MB)
            if logo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Logo size must be less than 2MB.")
        return logo


class CompanyVerificationForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['verification_status', 'rejection_reason']
        widgets = {
            'verification_status': forms.Select(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md'
            }),
            'rejection_reason': forms.Textarea(attrs={
                'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md h-28 resize-none',
                'rows': 3,
                'placeholder': 'Enter reason for rejection (required if rejecting)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rejection_reason'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        verification_status = cleaned_data.get('verification_status')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        if verification_status == 'rejected' and not rejection_reason:
            raise forms.ValidationError("Please provide a reason for rejection.")
        
        return cleaned_data


from django import forms
from django.contrib.auth.models import User
from .models import EmployeeRole


class InviteEmployeeForm(forms.Form):

    invited_email = forms.EmailField(
        label='Email Address'
    )

    role = forms.ChoiceField(
        label='Role'
    )

    def __init__(self, *args, **kwargs):

        company = kwargs.pop('company', None)
        current_employee = kwargs.pop('current_employee', None)

        super().__init__(*args, **kwargs)

        roles = EmployeeRole.objects.filter(company=company)

        # Restrict admin invitation
        if (
            current_employee
            and current_employee.role.name != 'company_admin'
        ):
            roles = roles.exclude(name='company_admin')

        self.fields['role'].choices = [
            (role.id, role.get_name_display())
            for role in roles
        ]

        self.fields['invited_email'].widget.attrs.update({
            'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md w-full',
            'placeholder': 'colleague@example.com'
        })

        self.fields['role'].widget.attrs.update({
            'class': 'vd hh rg zk _g ch hm dm fm pl/50 xi mi sm xm pm dn/40 rounded-md w-full',
            'id': 'id_role'
        })

    def clean_invited_email(self):

        email = self.cleaned_data.get('invited_email')

        if not User.objects.filter(email=email).exists():

            raise forms.ValidationError(
                "User with this email does not have an account."
            )

        return email
    

class CompanyApprovalForm(forms.Form):
    """Form for approving a company"""
    action = forms.CharField(widget=forms.HiddenInput(), initial='approve')
    company_id = forms.IntegerField(widget=forms.HiddenInput())


class CompanyRejectionForm(forms.Form):
    """Form for rejecting a company"""
    action = forms.CharField(widget=forms.HiddenInput(), initial='reject')
    company_id = forms.IntegerField(widget=forms.HiddenInput())
    rejection_reason = forms.CharField(
        label="Rejection Reason",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-3 py-2 border border-red-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent',
            'placeholder': 'Please provide a detailed reason for rejection...',
            'required': True
        }),
        required=True
    )