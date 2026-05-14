from django.views.generic import CreateView, DetailView, UpdateView, ListView, TemplateView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import secrets

from .models import Company, CompanyEmployee, EmployeeRole, CompanyInvitation
from .forms import CompanyRegistrationForm, CompanyVerificationForm, InviteEmployeeForm
from user.models import Notification

class CompanyRegistrationView(LoginRequiredMixin, CreateView):
    model = Company
    form_class = CompanyRegistrationForm
    template_name = 'company/company_registration.html'
    success_url = reverse_lazy('registration_success')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        company = self.object
        
        # Create company admin role
        admin_role, _ = EmployeeRole.objects.get_or_create(
            company=company,
            name='company_admin',
            defaults={
                'can_post_jobs': True,
                'can_edit_jobs': True,
                'can_view_applications': True,
                'can_manage_team': True
            }
        )
        
        # Create employee record for the user
        CompanyEmployee.objects.create(
            user=self.request.user,
            company=company,
            role=admin_role,
            designation='Company Admin'
        )
        self.request.user.profile.user_type = 'company_admin'
        self.request.user.profile.save()
        
        messages.success(self.request, 'Company registered successfully! Our team will verify your company soon.')
        return response


class CompanyRegistrationSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'company/registration_success.html'


class CompanySelectionView(LoginRequiredMixin, TemplateView):
    """View to select which company to manage (for users with multiple companies)"""
    template_name = 'company/company_selection.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all active employments for the user
        context['employments'] = CompanyEmployee.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('company', 'role').order_by('-joined_at')
        
        # Store the next URL if provided
        context['next'] = self.request.GET.get('next', '')
        
        return context


class CompanyDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'company/company_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Get company_id from URL or session
        company_id = kwargs.get('company_id') or request.session.get('current_company_id')
        
        if not company_id:
            # Store the current path to return after selection
            current_path = request.path
            return redirect(f"{reverse('company_selection')}?next={current_path}")
        
        # Get the employee record for this company
        self.employee = get_object_or_404(
            CompanyEmployee, 
            user=request.user, 
            company_id=company_id,
            is_active=True
        )
        
        # Store current company in session
        request.session['current_company_id'] = company_id
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.employee.company
        
        context['company'] = company
        context['employee'] = self.employee
        context['jobs'] = company.jobs.all()[:10]
        context['active_jobs_count'] = company.get_active_jobs_count()
        context['employees_count'] = company.employees.filter(is_active=True).count()
        context['applications_count'] = sum(job.applications.count() for job in company.jobs.all())
        
        # Get all companies the user is associated with for the switcher
        context['user_companies'] = CompanyEmployee.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related('company', 'role')
        
        # Pass current path for the switcher
        context['current_path'] = self.request.path
        
        return context


# company/views.py

class SwitchCompanyView(LoginRequiredMixin, RedirectView):
    """Switch between different companies"""
    
    def get_redirect_url(self, *args, **kwargs):
        company_id = kwargs.get('company_id')
        next_url = self.request.GET.get('next', '')
        
        # Verify user has access to this company
        employee = CompanyEmployee.objects.filter(
            user=self.request.user,
            company_id=company_id,
            is_active=True
        ).first()
        
        if employee:
            # Store in session
            self.request.session['current_company_id'] = company_id
            
            # If next_url is provided and valid, use it
            if next_url and next_url != 'None':
                return next_url
            
            # Otherwise go to dashboard
            return reverse('company_dashboard', kwargs={'company_id': company_id})
        else:
            messages.error(self.request, "You don't have access to this company.")
            return reverse('company_selection')

class CompanyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Company
    template_name = 'company/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(verification_status=status)
        return queryset


class CompanyDetailView(LoginRequiredMixin, DetailView):
    model = Company
    template_name = 'company/company_detail.html'
    context_object_name = 'company'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            context['verification_form'] = CompanyVerificationForm(instance=self.object)
        return context


class CompanyVerifyView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Company
    form_class = CompanyVerificationForm
    template_name = 'company/company_verify.html'
    success_url = reverse_lazy('company_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        response = super().form_valid(form)
        company = self.object
        
        if form.cleaned_data['verification_status'] == 'verified':
            company.verified_by = self.request.user
            company.verified_at = timezone.now()
            company.save()
            
            # Send email to all company admins
            admins = company.employees.filter(role__name='company_admin')
            for admin in admins:
                if admin.user.email:
                    send_mail(
                        f'Company {company.name} Verified',
                        f'Your company {company.name} has been verified by our team. You can now post jobs.',
                        settings.DEFAULT_FROM_EMAIL,
                        [admin.user.email],
                        fail_silently=True,
                    )
            
            messages.success(self.request, f'Company {company.name} has been verified.')
        else:
            messages.success(self.request, f'Company {company.name} has been rejected.')
        
        return response

from django.views.generic.edit import FormView

class InviteEmployeeView(LoginRequiredMixin, FormView):
    form_class = InviteEmployeeForm
    template_name = 'company/invite_employee.html'

    def dispatch(self, request, *args, **kwargs):

        company_id = kwargs.get('company_id') or request.session.get('current_company_id')

        if not company_id:
            return redirect(
                f"{reverse('company_selection')}?next={request.path}"
            )

        self.employee = get_object_or_404(
            CompanyEmployee,
            user=request.user,
            company_id=company_id,
            is_active=True
        )

        if not self.employee.role.can_manage_team:
            messages.error(
                request,
                "You don't have permission to invite team members."
            )

            return redirect(
                'company_dashboard',
                company_id=self.employee.company.id
            )

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs['company'] = self.employee.company

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['company'] = self.employee.company
        context['employee'] = self.employee

        if self.employee.role.name == 'company_admin':
            context['available_roles'] = EmployeeRole.objects.filter(
                company=self.employee.company
            )
        else:
            context['available_roles'] = EmployeeRole.objects.filter(
                company=self.employee.company
            ).exclude(name='company_admin')

        return context

    def form_valid(self, form):

        invited_email = form.cleaned_data['invited_email']
        role_id = form.cleaned_data['role']

        role = EmployeeRole.objects.get(
            id=role_id,
            company=self.employee.company
        )

        existing_employee = CompanyEmployee.objects.filter(
            company=self.employee.company,
            user__email=invited_email
        ).first()

        if existing_employee:
            messages.error(
                self.request,
                'This user is already associated with your company.'
            )

            return self.form_invalid(form)

        existing_invitation = CompanyInvitation.objects.filter(
            company=self.employee.company,
            invited_email=invited_email,
            status='pending'
        ).first()

        if existing_invitation:
            messages.error(
                self.request,
                'An active invitation already exists for this email.'
            )

            return self.form_invalid(form)

        token = secrets.token_urlsafe(32)

        invitation = CompanyInvitation.objects.create(
            company=self.employee.company,
            invited_by=self.employee,
            invited_email=invited_email,
            role=role,
            token=token,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )

        accept_url = self.request.build_absolute_uri(
            reverse(
                'accept_invitation',
                kwargs={'token': token}
            )
        )

        # Send email notification
        send_mail(
            subject=f'Invitation to join {self.employee.company.name}',
            message=f"""
You have been invited to join {self.employee.company.name}
as {role.get_name_display()}.

Accept invitation:
{accept_url}

This invitation expires in 7 days.
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invited_email],
            fail_silently=False,
        )

        # Create in-app notification for the invited user
        # First, check if user exists with this email
        from django.contrib.auth.models import User
        invited_user = User.objects.filter(email=invited_email).first()
        
        if invited_user:
            # User exists, create notification for them
            Notification.objects.create(
                user=invited_user,
                notification_type='system',
                message=f'You have been invited to join {self.employee.company.name} as {role.get_name_display()}. Click to accept.',
                link=accept_url,
                related_object_id=str(invitation.id),
                related_model='CompanyInvitation'
            )
        else:
            # User doesn't exist yet, we can create a notification when they register
            # For now, we'll just rely on email
            pass

        messages.success(
            self.request,
            f'Invitation sent to {invited_email}'
        )

        return redirect(
            'company_dashboard',
            company_id=self.employee.company.id
        )

    def get_success_url(self):
        return reverse(
            'company_dashboard',
            kwargs={'company_id': self.employee.company.id}
        )

class AcceptInvitationView(LoginRequiredMixin, TemplateView):
    template_name = 'company/accept_invitation.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.invitation = get_object_or_404(CompanyInvitation, token=kwargs['token'])
        
        if not self.invitation.is_valid():
            messages.error(request, 'This invitation has expired or is no longer valid.')
            return redirect('home')
        
        # Check if user is already in company
        if CompanyEmployee.objects.filter(company=self.invitation.company, user=request.user).exists():
            messages.error(request, 'You are already a member of this company.')
            return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invitation'] = self.invitation
        return context
    
    def post(self, request, *args, **kwargs):
        # Accept invitation
        employee = CompanyEmployee.objects.create(
            user=request.user,
            company=self.invitation.company,
            role=self.invitation.role,
            designation=self.invitation.role.get_name_display(),
            is_active=True
        )
        
        self.invitation.status = 'accepted'
        self.invitation.save()
        
        messages.success(request, f'You have successfully joined {self.invitation.company.name}')
        
        # Create notification for the inviter
        inviter = self.invitation.invited_by
        if inviter and inviter.user:
            # Get the user's full name or username
            user_name = request.user.get_full_name() or request.user.username
            
            # Create notification
            Notification.objects.create(
                user=inviter.user,
                notification_type='invitation_accepted',
                message=f'{user_name} has accepted your invitation to join {self.invitation.company.name} as {self.invitation.role.get_name_display()}.',
                link=f'/company/{self.invitation.company.id}/employees/',
                related_object_id=str(employee.id),
                related_model='CompanyEmployee'
            )
        
        # Check if user has multiple companies
        user_companies_count = CompanyEmployee.objects.filter(user=request.user, is_active=True).count()
        
        if user_companies_count > 1:
            # Redirect to company selection
            return redirect('company_selection')
        else:
            # Store in session and go to dashboard
            request.session['current_company_id'] = self.invitation.company.id
            return redirect('company_dashboard', company_id=self.invitation.company.id)

class EmployeeListView(LoginRequiredMixin, ListView):
    template_name = 'company/team_members.html'  # Make sure this matches your template name
    context_object_name = 'employees'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        # Get company_id from URL or session
        company_id = kwargs.get('company_id') or request.session.get('current_company_id')
        
        if not company_id:
            return redirect(f"{reverse('company_selection')}?next={request.path}")
        
        self.employee = get_object_or_404(
            CompanyEmployee, 
            user=request.user, 
            company_id=company_id,
            is_active=True
        )
        
        if not self.employee.role.can_manage_team:
            messages.error(request, "You don't have permission to view team members.")
            return redirect('company_dashboard', company_id=self.employee.company.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = CompanyEmployee.objects.filter(
            company=self.employee.company,
            is_active=True
        ).select_related('user', 'role').order_by('-joined_at')
        
        # Add search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(designation__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.employee.company
        context['user_role'] = self.employee.role
        context['search_query'] = self.request.GET.get('search', '')
        context['total_employees'] = self.get_queryset().count()
        return context
    

# company/views.py
from django.views.generic import ListView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.forms import ModelForm
from .forms import CompanyApprovalForm, CompanyRejectionForm
import logging

logger = logging.getLogger(__name__)


class CompanyApprovalListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for admins to see companies pending approval
    """
    model = Company
    template_name = 'company/company_approval_list.html'
    context_object_name = 'companies'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff
    
    def get_queryset(self):
        queryset = Company.objects.filter(
            verification_status='pending'
        ).select_related('verified_by').annotate(
            employee_count=Count('employees', distinct=True),
            job_count=Count('jobs', distinct=True)
        ).order_by('created_at')
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(registration_number__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(state__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['pending_count'] = Company.objects.filter(verification_status='pending').count()
        context['verified_count'] = Company.objects.filter(verification_status='verified').count()
        context['rejected_count'] = Company.objects.filter(verification_status='rejected').count()
        context['suspended_count'] = Company.objects.filter(verification_status='suspended').count()
        context['search_query'] = self.request.GET.get('search', '')
        
        # Initialize forms for modal
        context['approval_form'] = CompanyApprovalForm()
        context['rejection_form'] = CompanyRejectionForm()
        
        return context


class CompanyApproveView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View for approving a company"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff
    
    def post(self, request, *args, **kwargs):
        form = CompanyApprovalForm(request.POST)
        
        if form.is_valid():
            company_id = form.cleaned_data['company_id']
            company = get_object_or_404(Company, id=company_id)
            
            company.verification_status = 'verified'
            company.verified_by = request.user
            company.verified_at = timezone.now()
            company.rejection_reason = None
            company.save()
            
            # Create default admin role
            try:
                admin_role, created = EmployeeRole.objects.get_or_create(
                    company=company,
                    name='company_admin',
                    defaults={
                        'can_post_jobs': True,
                        'can_edit_jobs': True,
                        'can_view_applications': True,
                        'can_manage_team': True
                    }
                )
                
                first_employee = CompanyEmployee.objects.filter(company=company).first()
                if first_employee:
                    first_employee.role = admin_role
                    first_employee.save()
                    
            except Exception as e:
                logger.error(f"Error creating admin role: {str(e)}")
            
            messages.success(request, f'Company "{company.name}" has been approved!')
            
        else:
            messages.error(request, 'Invalid form submission.')
        
        return redirect('company_approval_list')


class CompanyRejectView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View for rejecting a company"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff
    
    def post(self, request, *args, **kwargs):
        form = CompanyRejectionForm(request.POST)
        
        if form.is_valid():
            company_id = form.cleaned_data['company_id']
            rejection_reason = form.cleaned_data['rejection_reason']
            company = get_object_or_404(Company, id=company_id)
            
            company.verification_status = 'rejected'
            company.verified_by = request.user
            company.verified_at = timezone.now()
            company.rejection_reason = rejection_reason
            company.save()
            
            messages.warning(request, f'Company "{company.name}" has been rejected.')
            
        else:
            messages.error(request, 'Please provide a valid rejection reason.')
        
        return redirect('company_approval_list')
    
class RemoveEmployeeView(LoginRequiredMixin, View):
    """View to remove an employee from company"""
    
    def post(self, request, company_id, employee_id):
        # Get the company
        company = get_object_or_404(Company, id=company_id)
        
        # Get the current user's employee record
        current_employee = get_object_or_404(
            CompanyEmployee,
            user=request.user,
            company=company,
            is_active=True
        )
        
        # Check if current user has permission to manage team
        if not current_employee.role.can_manage_team:
            messages.error(request, "You don't have permission to remove team members.")
            return redirect('employee_list', company_id=company.id)
        
        # Get the employee to remove
        employee_to_remove = get_object_or_404(
            CompanyEmployee,
            id=employee_id,
            company=company,
            is_active=True
        )
        
        # Prevent removing yourself
        if employee_to_remove.user == request.user:
            messages.error(request, "You cannot remove yourself from the company.")
            return redirect('employee_list', company_id=company.id)
        
        # Deactivate the employee
        employee_to_remove.is_active = False
        employee_to_remove.save()
        
        messages.success(
            request, 
            f'{employee_to_remove.user.get_full_name|default:employee_to_remove.user.username} has been removed from the company.'
        )
        
        return redirect('employee_list', company_id=company.id)
    
from django.db.models import Q
from jobs.models import Job
from django.core.paginator import Paginator
class CompanyPreviewView(DetailView):
    """Public view of company with its jobs"""
    model = Company
    template_name = 'company/company_preview.html'
    context_object_name = 'company'
    pk_url_kwarg = 'company_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()
        
        # Get active jobs for this company
        jobs = Job.objects.filter(
            company=company,
            is_active=True,
            is_approved=True,
            company__verification_status='verified'
        ).order_by('-created_at')
        
        # Apply filters
        title = self.request.GET.get('title')
        location = self.request.GET.get('location')
        job_type = self.request.GET.get('job_type')
        work_mode = self.request.GET.get('work_mode')
        experience_level = self.request.GET.get('experience_level')
        
        if title:
            jobs = jobs.filter(title__icontains=title)
        if location:
            jobs = jobs.filter(location__icontains=location)
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        if work_mode:
            jobs = jobs.filter(work_mode=work_mode)
        if experience_level:
            jobs = jobs.filter(experience_level=experience_level)
        
        # Pagination
        paginator = Paginator(jobs, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['jobs'] = page_obj
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context['paginator'] = paginator
        context['active_jobs_count'] = Job.objects.filter(
            company=company,
            is_active=True,
            is_approved=True,
            company__verification_status='verified'
        ).count()
        context['employees_count'] = company.employees.filter(is_active=True).count()
        
        return context