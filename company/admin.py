
# company/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count
from .models import Company, EmployeeRole, CompanyEmployee, CompanyInvitation

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'registration_number', 'verification_status', 'is_verified_display', 'email', 'phone', 'created_at', 'jobs_count']
    list_filter = ['verification_status', 'country', 'created_at']
    search_fields = ['name', 'registration_number', 'email', 'phone', 'city']
    readonly_fields = ['created_at', 'updated_at', 'verified_at', 'get_document_links', 'get_logo_preview']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'registration_number', 'tax_id', 'logo', 'get_logo_preview')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code')
        }),
        ('Verification', {
            'fields': ('verification_status', 'verified_by', 'verified_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Documents', {
            'fields': ('registration_document', 'tax_document', 'get_document_links'),
            'classes': ('collapse',)
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', obj.logo.url)
        return "No logo uploaded"
    get_logo_preview.short_description = 'Logo Preview'
    
    def get_document_links(self, obj):
        links = []
        if obj.registration_document:
            links.append(format_html('<a href="{}" target="_blank">Registration Document</a>', obj.registration_document.url))
        if obj.tax_document:
            links.append(format_html('<a href="{}" target="_blank">Tax Document</a>', obj.tax_document.url))
        return format_html('<br>'.join(links)) if links else "No documents uploaded"
    get_document_links.short_description = 'Documents'
    
    def is_verified_display(self, obj):
        if obj.is_verified():
            return format_html('<span style="color: green;">✓ Verified</span>')
        return format_html('<span style="color: red;">✗ Not Verified</span>')
    is_verified_display.short_description = 'Verified'
    
    def jobs_count(self, obj):
        return obj.jobs.count()
    jobs_count.short_description = 'Total Jobs'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(jobs_count=Count('jobs'))
    
    actions = ['approve_companies', 'reject_companies', 'suspend_companies']
    
    @admin.action(description='Approve selected companies')
    def approve_companies(self, request, queryset):
        for company in queryset:
            company.verification_status = 'verified'
            company.verified_at = timezone.now()
            company.verified_by = request.user
            company.rejection_reason = None
            company.save()
        self.message_user(request, f'{queryset.count()} companies approved successfully.')
    
    @admin.action(description='Reject selected companies')
    def reject_companies(self, request, queryset):
        for company in queryset:
            company.verification_status = 'rejected'
            company.verified_at = timezone.now()
            company.verified_by = request.user
            company.save()
        self.message_user(request, f'{queryset.count()} companies rejected.')
    
    @admin.action(description='Suspend selected companies')
    def suspend_companies(self, request, queryset):
        for company in queryset:
            company.verification_status = 'suspended'
            company.save()
        self.message_user(request, f'{queryset.count()} companies suspended.')
    
    def save_model(self, request, obj, form, change):
        if 'verification_status' in form.changed_data and obj.verification_status == 'verified':
            obj.verified_by = request.user
            obj.verified_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(EmployeeRole)
class EmployeeRoleAdmin(admin.ModelAdmin):
    list_display = ['company', 'name_display', 'can_post_jobs', 'can_edit_jobs', 'can_view_applications', 'can_manage_team']
    list_filter = ['company', 'name', 'can_post_jobs', 'can_edit_jobs']
    search_fields = ['company__name', 'name']
    
    def name_display(self, obj):
        return obj.get_name_display()
    name_display.short_description = 'Role Name'
    
    fieldsets = (
        ('Role Information', {
            'fields': ('company', 'name')
        }),
        ('Permissions', {
            'fields': ('can_post_jobs', 'can_edit_jobs', 'can_view_applications', 'can_manage_team'),
            'description': 'Define what this role can do within the company'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


@admin.register(CompanyEmployee)
class CompanyEmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_link', 'role_display', 'designation', 'department', 'is_active', 'joined_at']
    list_filter = ['company', 'role', 'is_active', 'department', 'joined_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'company__name', 'designation']
    readonly_fields = ['joined_at', 'user_link', 'company_link_detail']
    
    def company_link(self, obj):
        url = reverse('admin:company_company_change', args=[obj.company.id])
        return format_html('<a href="{}">{}</a>', url, obj.company.name)
    company_link.short_description = 'Company'
    
    def company_link_detail(self, obj):
        url = reverse('admin:company_company_change', args=[obj.company.id])
        return format_html('<a href="{}" target="_blank">View Company Details</a>', url)
    company_link_detail.short_description = 'Company Details'
    
    def user_link(self, obj):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def role_display(self, obj):
        return obj.role.get_name_display()
    role_display.short_description = 'Role'
    
    def can_post_jobs_display(self, obj):
        if obj.can_post_jobs():
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    can_post_jobs_display.short_description = 'Can Post Jobs'
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('user', 'user_link', 'company', 'company_link_detail', 'role')
        }),
        ('Job Details', {
            'fields': ('employee_id', 'designation', 'department')
        }),
        ('Status', {
            'fields': ('is_active', 'joined_at')
        }),
        ('Permissions Summary', {
            'fields': ('can_post_jobs_display',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'company', 'role')
    
    actions = ['activate_employees', 'deactivate_employees']
    
    @admin.action(description='Activate selected employees')
    def activate_employees(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} employees activated.')
    
    @admin.action(description='Deactivate selected employees')
    def deactivate_employees(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} employees deactivated.')


@admin.register(CompanyInvitation)
class CompanyInvitationAdmin(admin.ModelAdmin):
    list_display = ['invited_email', 'company_link', 'invited_by_info', 'role_display', 'status', 'is_valid_display', 'expires_at', 'created_at']
    list_filter = ['status', 'company', 'role', 'expires_at', 'created_at']
    search_fields = ['invited_email', 'company__name', 'invited_by__user__email', 'token']
    readonly_fields = ['token', 'created_at', 'invitation_link']
    
    def company_link(self, obj):
        url = reverse('admin:company_company_change', args=[obj.company.id])
        return format_html('<a href="{}">{}</a>', url, obj.company.name)
    company_link.short_description = 'Company'
    
    def invited_by_info(self, obj):
        return f"{obj.invited_by.user.username} ({obj.invited_by.role.get_name_display()})"
    invited_by_info.short_description = 'Invited By'
    
    def role_display(self, obj):
        return obj.role.get_name_display()
    role_display.short_description = 'Role'
    
    def is_valid_display(self, obj):
        if obj.is_valid():
            # Calculate days remaining
            days_remaining = (obj.expires_at - timezone.now()).days
            return format_html('<span style="color: green;">✓ Valid ({} days left)</span>', days_remaining)
        return format_html('<span style="color: red;">✗ Expired/Invalid</span>')
    is_valid_display.short_description = 'Valid'
    
    def invitation_link(self, obj):
        from django.conf import settings
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        url = f"{base_url}/company/invite/accept/{obj.token}/"
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    invitation_link.short_description = 'Invitation URL'
    
    fieldsets = (
        ('Invitation Details', {
            'fields': ('invited_email', 'company', 'company_link', 'role')
        }),
        ('Inviter Information', {
            'fields': ('invited_by', 'invited_by_info')
        }),
        ('Status & Token', {
            'fields': ('status', 'token', 'invitation_link', 'is_valid_display')
        }),
        ('Timeline', {
            'fields': ('expires_at', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'invited_by__user', 'role')
    
    actions = ['resend_invitations', 'cancel_invitations']
    
    @admin.action(description='Resend selected invitations')
    def resend_invitations(self, request, queryset):
        from django.core.mail import send_mail
        from django.conf import settings
        
        resent_count = 0
        for invitation in queryset.filter(status='pending'):
            # Resend email logic here
            accept_url = request.build_absolute_uri(
                reverse('accept_invitation', kwargs={'token': invitation.token})
            )
            send_mail(
                f'Invitation to join {invitation.company.name}',
                f"""
                You have been invited to join {invitation.company.name} as {invitation.role.get_name_display()}.
                
                Click here to accept: {accept_url}
                
                This invitation expires in 7 days.
                """,
                settings.DEFAULT_FROM_EMAIL,
                [invitation.invited_email],
                fail_silently=True,
            )
            resent_count += 1
        self.message_user(request, f'{resent_count} invitations resent.')
    
    @admin.action(description='Cancel selected invitations')
    def cancel_invitations(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} invitations cancelled.')