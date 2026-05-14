# jobs/views.py
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User

from .models import Job, JOB_TYPE_CHOICES, WORK_MODE_CHOICES, EXPERIENCE_LEVEL, CURRENCY_CHOICES
from .forms import JobForm
from company.models import CompanyEmployee
import logging
logger = logging.getLogger(__name__)


# jobs/views.py

import logging
logger = logging.getLogger(__name__)

class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/create_job.html'
    login_url = 'login'

    def dispatch(self, request, *args, **kwargs):
        """Check if user has permission to post jobs"""
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Get company_id from URL parameter (explicit selection)
        company_id = request.GET.get('company_id')
        
        # If no company_id, check session
        if not company_id:
            company_id = request.session.get('current_company_id')
        
        # If still no company_id, try to get user's companies
        if not company_id:
            user_companies = CompanyEmployee.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('company', 'role')
            
            if user_companies.count() == 0:
                messages.error(
                    request, 
                    "You are not associated with any company. Please register a company first."
                )
                return redirect('register_company')
            
            elif user_companies.count() == 1:
                company_id = user_companies.first().company.id
            else:
                # Store current path to return after selection
                request.session['job_post_return_url'] = request.path
                messages.info(request, "Please select a company to post a job.")
                return redirect(f"{reverse('company_selection')}?next={request.path}")
        
        # Get the employee record for the selected company
        self.employee = CompanyEmployee.objects.filter(
            user=request.user,
            company_id=company_id,
            is_active=True
        ).select_related('company', 'role').first()
        
        if not self.employee:
            messages.error(
                request, 
                "You are not associated with this company or your employment is not active."
            )
            return redirect('company_selection')
        
        # Store in session for future requests
        request.session['current_company_id'] = company_id
        
        # Check permissions
        if not self.employee.role.can_post_jobs:
            messages.error(
                request, 
                f"Your role '{self.employee.role.get_name_display()}' doesn't have permission to post jobs."
            )
            return redirect('company_dashboard', company_id=self.employee.company.id)
        
        # Check if company is verified
        if not self.employee.company.is_verified():
            messages.error(
                request, 
                f"Your company '{self.employee.company.name}' is not verified yet. "
                "Please wait for verification to post jobs."
            )
            return redirect('company_dashboard', company_id=self.employee.company.id)
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Set company and posted_by from the employee record"""
        try:
            # Set the company and posted_by
            form.instance.company = self.employee.company
            form.instance.posted_by = self.employee
            form.instance.is_active = True
            
            # Auto-approve since company is verified
            form.instance.is_approved = True
            form.instance.approved_by = self.employee  # Auto-approve by the poster
            form.instance.approved_at = timezone.now()
            
            # Log the data being saved
            logger.info(f"Creating job for company: {self.employee.company.name}")
            logger.info(f"Form data: {form.cleaned_data}")
            
            # Save the job
            response = super().form_valid(form)
            
            messages.success(
                self.request, 
                f"Job '{form.instance.title}' posted successfully and is now live!"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            messages.error(self.request, f"Error creating job: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submission"""
        # Log form errors
        logger.error(f"Form errors: {form.errors}")
        
        # Display form errors to user
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('job_detail', kwargs={'job_id': self.object.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'employee') and self.employee:
            context['company'] = self.employee.company
            context['employee'] = self.employee
            
            # Get all companies for the switcher
            context['user_companies'] = CompanyEmployee.objects.filter(
                user=self.request.user,
                is_active=True
            ).select_related('company', 'role')
            
            # Get current path for return URL
            context['current_path'] = self.request.path
            
        return context


class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/edit_job.html'
    pk_url_kwarg = 'job_id'
    
    def test_func(self):
        """Check if user can edit this job"""
        job = self.get_object()
        return job.can_be_edited_by(self.request.user)
    
    def form_valid(self, form):
        """Keep job approved since company is verified"""
        response = super().form_valid(form)
        
        # Keep the job approved since company is verified
        # Only update the approval timestamp to reflect the edit
        if self.object.is_approved:
            self.object.approved_at = timezone.now()
            self.object.save()
            messages.success(
                self.request, 
                "Job updated successfully! The changes are now live."
            )
        else:
            # If for some reason it wasn't approved, approve it now
            self.object.is_approved = True
            self.object.approved_by = self.request.user if hasattr(self, 'employee') else None
            self.object.approved_at = timezone.now()
            self.object.save()
            messages.success(
                self.request, 
                "Job updated and approved successfully!"
            )
        
        return response
    
    def get_success_url(self):
        return reverse_lazy('job_detail', kwargs={'job_id': self.object.id})

class JobListView(ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        # Show only published jobs (approved, active, from verified companies)
        queryset = Job.objects.filter(
            is_active=True,
            is_approved=True,
            company__verification_status='verified'
        ).select_related('company', 'posted_by__user')

        # Apply filters
        title = self.request.GET.get('title')
        location = self.request.GET.get('location')
        job_type = self.request.GET.get('job_type')
        work_mode = self.request.GET.get('work_mode')
        experience_level = self.request.GET.get('experience_level')
        salary_min = self.request.GET.get('salary_min')
        salary_max = self.request.GET.get('salary_max')
        skills = self.request.GET.get('skills')
        currency = self.request.GET.get('currency')

        if title:
            queryset = queryset.filter(title__icontains=title)

        if location:
            queryset = queryset.filter(location__icontains=location)

        if job_type:
            queryset = queryset.filter(job_type=job_type)

        if work_mode:
            queryset = queryset.filter(work_mode=work_mode)

        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)

        if salary_min:
            queryset = queryset.filter(salary_min__gte=salary_min)

        if salary_max:
            queryset = queryset.filter(salary_max__lte=salary_max)

        if skills:
            queryset = queryset.filter(skills_required__icontains=skills)

        if currency:
            queryset = queryset.filter(currency=currency)

        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job_type_choices'] = JOB_TYPE_CHOICES
        context['work_mode_choices'] = WORK_MODE_CHOICES
        context['experience_level_choices'] = EXPERIENCE_LEVEL
        context['currency_choices'] = CURRENCY_CHOICES
        return context


# jobs/views.py

class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'
    pk_url_kwarg = 'job_id'

    def get_queryset(self):
        # Show published jobs to everyone, show all to staff/recruiters
        if self.request.user.is_staff:
            return Job.objects.all()
        
        # Check if user is recruiter for this job
        if self.request.user.is_authenticated:
            employee = CompanyEmployee.objects.filter(
                user=self.request.user, 
                is_active=True
            ).first()
            if employee:
                return Job.objects.filter(
                    Q(is_active=True, is_approved=True, company__verification_status='verified') | 
                    Q(company=employee.company)
                )
        
        # Show only published jobs (active, approved, from verified companies)
        return Job.objects.filter(
            is_active=True,
            is_approved=True,
            company__verification_status='verified'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        
        # Check if user has already applied
        has_applied = False
        if self.request.user.is_authenticated:
            has_applied = job.applications.filter(
                user=self.request.user,
                status__in=['submitted', 'reviewed', 'shortlisted', 'interviewed', 'offered']
            ).exists()
        
        # Get similar jobs
        similar_jobs = Job.objects.filter(
            is_active=True,
            is_approved=True,
            company__verification_status='verified'
        ).exclude(pk=job.pk).filter(
            Q(title__icontains=job.title.split()[0] if job.title else '') |
            Q(skills_required__icontains=job.skills_required.split(',')[0] if job.skills_required else '') |
            Q(location__icontains=job.location.split()[0] if job.location else '')
        ).order_by('-created_at')[:5]
        
        # Get recent jobs
        recent_jobs = Job.objects.filter(
            is_active=True,
            is_approved=True,
            company__verification_status='verified'
        ).exclude(pk=job.pk).order_by('-created_at')[:5]
        
        # Check if user can edit
        can_edit = False
        if self.request.user.is_authenticated:
            can_edit = job.can_be_edited_by(self.request.user)
        
        # Add is_application_open to context
        context['is_application_open'] = job.is_application_open()
        context['similar_jobs'] = similar_jobs
        context['recent_jobs'] = recent_jobs
        context['has_applied'] = has_applied
        context['can_edit'] = can_edit
        context['is_recruiter'] = hasattr(self.request.user, 'employments') and self.request.user.employments.filter(company=job.company).exists()
        
        # Add current date for deadline comparison
        from django.utils import timezone
        context['now'] = timezone.now()
        
        return context


class UserJobsListView(LoginRequiredMixin, ListView):
    """
    View to list all jobs posted by a specific user (recruiter)
    URL: /jobs/user/<int:user_id>/
    """
    model = Job
    template_name = 'jobs/user_jobs.html'
    context_object_name = 'jobs'
    paginate_by = 10
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        
        # Get jobs posted by this user through CompanyEmployee
        queryset = Job.objects.filter(
            posted_by__user=user,
            is_active=True
        ).select_related('company').order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id')
        context['profile_user'] = get_object_or_404(User, id=user_id)
        context['is_owner'] = self.request.user.id == user_id
        return context


class CompanyJobsListView(LoginRequiredMixin, ListView):
    """
    View to list all jobs for the logged-in user's company
    """
    model = Job
    template_name = 'jobs/company_jobs.html'
    context_object_name = 'jobs'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        self.employee = CompanyEmployee.objects.filter(
            user=request.user, 
            is_active=True
        ).first()
        
        if not self.employee:
            messages.error(request, "You are not associated with any company.")
            return redirect('job_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Job.objects.filter(
            company=self.employee.company
        ).select_related('posted_by__user').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.employee.company
        context['employee'] = self.employee
        context['can_post_jobs'] = self.employee.can_post_jobs()
        return context


class JobApprovalListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for website admins to see jobs pending approval
    """
    model = Job
    template_name = 'jobs/job_approval_list.html'
    context_object_name = 'jobs'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return Job.objects.filter(
            is_approved=False,
            is_active=True,
            company__verification_status='verified'
        ).select_related('company', 'posted_by__user').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = self.get_queryset().count()
        return context


class JobApproveView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for website admins to approve/reject jobs
    """
    model = Job
    fields = []
    template_name = 'jobs/job_approve.html'
    pk_url_kwarg = 'job_id'
    success_url = reverse_lazy('job_approval_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request, *args, **kwargs):
        job = self.get_object()
        action = request.POST.get('action')
        
        if action == 'approve':
            job.is_approved = True
            job.approved_by = request.user
            job.approved_at = timezone.now()
            job.rejection_reason = None
            messages.success(request, f'Job "{job.title}" has been approved and is now live.')
            
        elif action == 'reject':
            job.is_approved = False
            job.approved_by = None
            job.approved_at = None
            job.rejection_reason = request.POST.get('rejection_reason', '')
            messages.warning(request, f'Job "{job.title}" has been rejected.')
        
        job.save()
        return redirect(self.success_url)