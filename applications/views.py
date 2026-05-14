from django.views.generic import ListView, UpdateView, DeleteView, CreateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.db.models import Q, Avg
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from .models import (
    Resume, Education, Experience, Skill,
    ProfessionalSummary, Link, Certification, Project, JobApplication,
    ApplicationNote, ApplicationActivity, GitHubContribution, GitHubStats
)
from .forms import (
    ResumeForm, EducationForm, ExperienceForm, SkillForm,
    ProfessionalSummaryForm, LinkForm,
    CertificationForm, ProjectForm, JobApplicationForm, ResumeUploadForm
)
from jobs.models import Job
from company.models import CompanyEmployee
import os
import logging

logger = logging.getLogger(__name__)


# ==================== MIXINS ====================

class CheckExistingApplicationMixin:
    """Mixin to check if user has already applied for a specific job"""
    
    def dispatch(self, request, *args, **kwargs):
        job_id = request.GET.get('job') or kwargs.get('job_id')
        if job_id:
            try:
                job = Job.objects.get(id=job_id)
                
                # Check for existing application
                existing_application = JobApplication.objects.filter(
                    user=request.user,
                    job=job
                ).exclude(status='withdrawn').first()
                
                if existing_application:
                    return render(request, 'applications/already_applied.html', {
                        'job': job,
                        'application': existing_application
                    })
            except Job.DoesNotExist:
                pass
        
        return super().dispatch(request, *args, **kwargs)


class RecruiterRequiredMixin(UserPassesTestMixin):
    """Mixin to check if user is a recruiter or staff"""
    
    def test_func(self):
        if self.request.user.is_staff:
            return True
        
        # Check if user has a company employee role with view applications permission
        if hasattr(self.request.user, 'employments'):
            employee = self.request.user.employments.filter(is_active=True).first()
            if employee and employee.can_view_applications():
                return True
        
        return False


# ==================== RESUME VIEWS ====================

class ResumeListView(LoginRequiredMixin, ListView):
    model = Resume
    template_name = 'applications/resume_list.html'
    context_object_name = 'resumes'
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user).order_by('-is_default', '-uploaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'resume'
        return context


class ResumeCreateView(LoginRequiredMixin, CreateView):
    model = Resume
    form_class = ResumeForm
    template_name = 'applications/resume_form.html'
    
    def get_success_url(self):
        return reverse_lazy('resume-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # If this is the first resume, make it default
        if not Resume.objects.filter(user=self.request.user).exists():
            form.instance.is_default = True
        
        messages.success(self.request, 'Resume uploaded successfully!')
        return super().form_valid(form)


class ResumeUpdateView(LoginRequiredMixin, UpdateView):
    model = Resume
    form_class = ResumeForm
    template_name = 'applications/resume_form.html'
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('resume-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Resume updated successfully!')
        return super().form_valid(form)


class ResumeDeleteView(LoginRequiredMixin, DeleteView):
    model = Resume
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('resume-list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # If deleting default resume, set another as default
        if self.object.is_default:
            other_resume = Resume.objects.filter(user=request.user).exclude(id=self.object.id).first()
            if other_resume:
                other_resume.is_default = True
                other_resume.save()
        
        self.object.delete()
        messages.success(request, 'Resume deleted successfully!')
        return redirect(self.get_success_url())


class ResumeManageView(LoginRequiredMixin, TemplateView):
    """Manage all resumes with ability to set default"""
    template_name = 'applications/resume_manage.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resumes'] = Resume.objects.filter(user=self.request.user).order_by('-is_default', '-uploaded_at')
        context['upload_form'] = ResumeUploadForm()
        return context


class ResumeUploadView(LoginRequiredMixin, CreateView):
    model = Resume
    form_class = ResumeUploadForm
    template_name = 'applications/resume_upload.html'
    
    def get_success_url(self):
        return reverse_lazy('resume-manage')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # If this is the first resume, make it default
        if not Resume.objects.filter(user=self.request.user).exists():
            form.instance.is_default = True
        
        response = super().form_valid(form)
        messages.success(self.request, "Resume uploaded successfully.")
        return response


class SetDefaultResumeView(LoginRequiredMixin, UpdateView):
    model = Resume
    fields = []
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)
    
    def post(self, request, *args, **kwargs):
        resume = self.get_object()
        
        # Remove default from all other resumes
        Resume.objects.filter(user=request.user).update(is_default=False)
        
        # Set this as default
        resume.is_default = True
        resume.save()
        
        messages.success(request, f"{resume.title} is now your default resume.")
        return redirect('resume-manage')


# ==================== EDUCATION VIEWS ====================

class EducationListView(LoginRequiredMixin, ListView):
    model = Education
    template_name = 'applications/education_list.html'
    context_object_name = 'educations'
    
    def get_queryset(self):
        return Education.objects.filter(user=self.request.user).order_by('-end_year', '-start_year')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'education'
        return context


class EducationCreateView(LoginRequiredMixin, CreateView):
    model = Education
    form_class = EducationForm
    template_name = 'applications/education_form.html'
    
    def get_success_url(self):
        return reverse_lazy('education-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Education added successfully!')
        return super().form_valid(form)


class EducationUpdateView(LoginRequiredMixin, UpdateView):
    model = Education
    form_class = EducationForm
    template_name = 'applications/education_form.html'
    
    def get_queryset(self):
        return Education.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('education-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Education updated successfully!')
        return super().form_valid(form)


class EducationDeleteView(LoginRequiredMixin, DeleteView):
    model = Education
    template_name = 'applications/education_confirm_delete.html'
    
    def get_queryset(self):
        return Education.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('education-list')


# ==================== EXPERIENCE VIEWS ====================

class ExperienceListView(LoginRequiredMixin, ListView):
    model = Experience
    template_name = 'applications/experience_list.html'
    context_object_name = 'experiences'
    
    def get_queryset(self):
        return Experience.objects.filter(user=self.request.user).order_by('-start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'experience'
        return context


class ExperienceCreateView(LoginRequiredMixin, CreateView):
    model = Experience
    form_class = ExperienceForm
    template_name = 'applications/experience_form.html'
    
    def get_success_url(self):
        return reverse_lazy('experience-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Experience added successfully!')
        return super().form_valid(form)


class ExperienceUpdateView(LoginRequiredMixin, UpdateView):
    model = Experience
    form_class = ExperienceForm
    template_name = 'applications/experience_form.html'
    
    def get_queryset(self):
        return Experience.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('experience-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Experience updated successfully!')
        return super().form_valid(form)


class ExperienceDeleteView(LoginRequiredMixin, DeleteView):
    model = Experience
    template_name = 'applications/experience_confirm_delete.html'
    
    def get_queryset(self):
        return Experience.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('experience-list')


# ==================== SKILL VIEWS ====================

class SkillListView(LoginRequiredMixin, ListView):
    model = Skill
    template_name = 'applications/skill_list.html'
    context_object_name = 'skills'
    
    def get_queryset(self):
        return Skill.objects.filter(user=self.request.user).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'skill'
        return context


class SkillCreateView(LoginRequiredMixin, CreateView):
    model = Skill
    form_class = SkillForm
    template_name = 'applications/skill_form.html'
    
    def get_success_url(self):
        return reverse_lazy('skill-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Skill added successfully!')
        return super().form_valid(form)


class SkillUpdateView(LoginRequiredMixin, UpdateView):
    model = Skill
    form_class = SkillForm
    template_name = 'applications/skill_form.html'
    
    def get_queryset(self):
        return Skill.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('skill-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Skill updated successfully!')
        return super().form_valid(form)


class SkillDeleteView(LoginRequiredMixin, DeleteView):
    model = Skill
    template_name = 'applications/skill_confirm_delete.html'
    
    def get_queryset(self):
        return Skill.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('skill-list')


# ==================== PROFESSIONAL SUMMARY VIEWS ====================

class ProfessionalSummaryCreateView(LoginRequiredMixin, CreateView):
    model = ProfessionalSummary
    form_class = ProfessionalSummaryForm
    template_name = 'applications/summary_form.html'
    
    def get_success_url(self):
        return reverse_lazy('summary-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Professional summary added successfully!')
        return super().form_valid(form)


class ProfessionalSummaryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProfessionalSummary
    form_class = ProfessionalSummaryForm
    template_name = 'applications/summary_form.html'
    
    def get_queryset(self):
        return ProfessionalSummary.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('summary-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Professional summary updated successfully!')
        return super().form_valid(form)


class ProfessionalSummaryDeleteView(LoginRequiredMixin, DeleteView):
    model = ProfessionalSummary
    template_name = 'applications/summary_confirm_delete.html'
    
    def get_queryset(self):
        return ProfessionalSummary.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('summary-list')


# ==================== LINK VIEWS ====================

class LinkListView(LoginRequiredMixin, ListView):
    model = Link
    template_name = 'applications/link_list.html'
    context_object_name = 'links'
    
    def get_queryset(self):
        return Link.objects.filter(user=self.request.user).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'link'
        return context


class LinkCreateView(LoginRequiredMixin, CreateView):
    model = Link
    form_class = LinkForm
    template_name = 'applications/link_form.html'
    
    def get_success_url(self):
        return reverse_lazy('link-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Link added successfully!')
        return super().form_valid(form)


class LinkUpdateView(LoginRequiredMixin, UpdateView):
    model = Link
    form_class = LinkForm
    template_name = 'applications/link_form.html'
    
    def get_queryset(self):
        return Link.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('link-list')


class LinkDeleteView(LoginRequiredMixin, DeleteView):
    model = Link
    template_name = 'applications/link_confirm_delete.html'
    
    def get_queryset(self):
        return Link.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('link-list')


# ==================== CERTIFICATION VIEWS ====================

class CertificationListView(LoginRequiredMixin, ListView):
    model = Certification
    template_name = 'applications/certification_list.html'
    context_object_name = 'certifications'
    
    def get_queryset(self):
        return Certification.objects.filter(user=self.request.user).order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'certification'
        return context


class CertificationCreateView(LoginRequiredMixin, CreateView):
    model = Certification
    form_class = CertificationForm
    template_name = 'applications/certification_form.html'
    
    def get_success_url(self):
        return reverse_lazy('certification-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Certification added successfully!')
        return super().form_valid(form)


class CertificationUpdateView(LoginRequiredMixin, UpdateView):
    model = Certification
    form_class = CertificationForm
    template_name = 'applications/certification_form.html'
    
    def get_queryset(self):
        return Certification.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('certification-list')


class CertificationDeleteView(LoginRequiredMixin, DeleteView):
    model = Certification
    template_name = 'applications/certification_confirm_delete.html'
    
    def get_queryset(self):
        return Certification.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('certification-list')


# ==================== PROJECT VIEWS ====================

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'applications/project_list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        return Project.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'project'
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'applications/project_form.html'
    
    def get_success_url(self):
        return reverse_lazy('project-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Project added successfully!')
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'applications/project_form.html'
    
    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('project-list')


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'applications/project_confirm_delete.html'
    
    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('project-list')


class ApplyJobView(LoginRequiredMixin, CreateView):
    """Direct job application view - submit or save draft in one go"""
    model = JobApplication
    fields = []  # We'll handle manually
    template_name = 'applications/job_application_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.job = get_object_or_404(Job, pk=kwargs['pk'])
        
        # Check if job is available
        if not self.job.is_published():
            messages.error(request, "This job is not available for application.")
            return redirect('job_detail', job_id=self.job.pk)
        
        # Check deadline
        if self.job.application_deadline and self.job.application_deadline < timezone.now().date():
            messages.error(request, "Application deadline has passed.")
            return redirect('job_detail', job_id=self.job.pk)
        
        # Check if already applied (excluding withdrawn applications)
        # Allow re-application if previous application was withdrawn
        existing_application = JobApplication.objects.filter(
            user=request.user, 
            job=self.job
        ).exclude(status='withdrawn').first()  # Exclude withdrawn status
        
        if existing_application:
            messages.error(request, "You have already applied for this position.")
            return redirect('job_detail', job_id=self.job.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.job
        context['resumes'] = Resume.objects.filter(user=self.request.user).order_by('-is_default', '-uploaded_at')
        context['has_resumes'] = context['resumes'].exists()
        return context
    
    def post(self, request, *args, **kwargs):
        resume_id = request.POST.get('selected_resume')
        action = request.POST.get('action')  # 'submit' or 'draft'
        cover_letter = request.POST.get('cover_letter', '')
        
        # Validate resume
        if not resume_id:
            messages.error(request, "Please select a resume to continue.")
            return redirect('apply', pk=self.job.pk)
        
        try:
            resume = Resume.objects.get(id=resume_id, user=request.user)
        except Resume.DoesNotExist:
            messages.error(request, "Selected resume does not exist.")
            return redirect('apply', pk=self.job.pk)
        
        # Check if there's an existing withdrawn application
        existing_withdrawn = JobApplication.objects.filter(
            user=request.user,
            job=self.job,
            status='withdrawn'
        ).first()
        
        if existing_withdrawn:
            # Update the existing withdrawn application instead of creating new
            existing_withdrawn.resume = resume
            existing_withdrawn.cover_letter = cover_letter
            existing_withdrawn.status = 'submitted' if action == 'submit' else 'draft'
            existing_withdrawn.updated_at = timezone.now()
            
            # Reset ATS analysis for re-application
            existing_withdrawn.ats_score = None
            existing_withdrawn.ats_analysis_status = 'pending'
            existing_withdrawn.ats_analysis_started_at = None
            existing_withdrawn.ats_analysis_completed_at = None
            existing_withdrawn.save()
            
            application = existing_withdrawn
            
            if action == 'submit':
                messages.success(request, "Your application has been re-submitted successfully!")
            else:
                messages.success(request, "Application saved as draft.")
        else:
            # Create new application
            application = JobApplication.objects.create(
                user=request.user,
                job=self.job,
                resume=resume,
                cover_letter=cover_letter,
                status='submitted' if action == 'submit' else 'draft'
            )
            
            if action == 'submit':
                messages.success(request, "Your application has been submitted successfully!")
            else:
                messages.success(request, "Application saved as draft. You can submit it later from your dashboard.")
        
        # Log activity
        ApplicationActivity.objects.create(
            application=application,
            action='application_created' if not existing_withdrawn else 'application_re_submitted',
            performed_by=request.user,
            details={'status': application.status}
        )
        
        # Trigger ATS analysis for submitted applications (including re-submitted ones)
        if action == 'submit':
            try:
                from .ats_integration import run_ats_analysis_async
                application.ats_analysis_status = 'processing'
                application.ats_analysis_started_at = timezone.now()
                application.save()
                run_ats_analysis_async(application.id)
                logger.info(f"ATS analysis triggered for application {application.id}")
            except ImportError as e:
                logger.warning(f"ATS integration not available: {e}")
            except Exception as e:
                logger.error(f"Failed to trigger ATS analysis: {e}")
        
        return redirect('my-applications')


# applications/views.py
class MyApplicationsView(LoginRequiredMixin, ListView):
    """View all my applications"""
    model = JobApplication
    template_name = 'applications/job_application_list.html'
    context_object_name = 'applications'
    paginate_by = 10
    
    def get_queryset(self):
        return JobApplication.objects.filter(
            user=self.request.user
        ).select_related(
            'job', 
            'job__company', 
            'resume', 
            'ats_score'
        ).prefetch_related(
            'notes', 
            'notes__added_by'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applications = JobApplication.objects.filter(user=self.request.user)
        context['draft_count'] = applications.filter(status='draft').count()
        context['submitted_count'] = applications.filter(status='submitted').count()
        context['ats_completed_count'] = applications.filter(
            ats_analysis_status='completed', 
            ats_score__isnull=False
        ).count()
        return context


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    """View application details"""
    model = JobApplication
    template_name = 'applications/application_detail.html'
    context_object_name = 'application'
    
    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.object
        context['can_withdraw'] = application.status in ['submitted', 'reviewed']
        context['can_submit'] = application.status == 'draft'
        context['activities'] = application.activities.all().order_by('-created_at')
        return context


class WithdrawApplicationView(LoginRequiredMixin, UpdateView):
    """Withdraw an application"""
    model = JobApplication
    fields = []
    template_name = 'applications/withdraw_confirm.html'
    
    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)
    
    def post(self, request, *args, **kwargs):
        application = self.get_object()
        
        # Allow withdrawal only for submitted applications (not reviewed)
        if application.status == 'submitted':
            application.status = 'withdrawn'
            application.save()
            
            ApplicationActivity.objects.create(
                application=application,
                action='application_withdrawn',
                performed_by=request.user,
                details={'withdrawn_at': str(timezone.now())}
            )
            messages.success(request, "Your application has been withdrawn. You can apply again if the job is still open.")
        else:
            if application.status == 'reviewed':
                messages.error(request, "Your application is already under review and cannot be withdrawn.")
            else:
                messages.error(request, "This application cannot be withdrawn.")
        
        return redirect('my-applications')


# applications/views.py

class RecruiterApplicationsListView(LoginRequiredMixin, ListView):
    model = JobApplication
    template_name = 'applications/recruiter_applications.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        self.job = get_object_or_404(Job, id=kwargs['job_id'])
        
        # Check if user has permission to view applications for this job
        if not request.user.is_staff:
            has_permission = False
            
            # Check if user is the job poster
            if self.job.posted_by and self.job.posted_by.user == request.user:
                has_permission = True
            
            # If not job poster, check if user is an employee of the company with permission
            if not has_permission and hasattr(request.user, 'employments'):
                employee = request.user.employments.filter(
                    is_active=True,
                    company=self.job.company
                ).first()
                
                if employee and employee.role.can_view_applications:
                    has_permission = True
            
            if not has_permission:
                messages.error(request, "You don't have permission to view these applications.")
                return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        from django.db.models import Q, Avg
        
        queryset = JobApplication.objects.filter(job=self.job).select_related(
            'user', 'job', 'resume', 'ats_score'
        )
        
        # Filter by applicant name
        applicant_name = self.request.GET.get('applicant_name')
        if applicant_name:
            queryset = queryset.filter(
                Q(user__first_name__icontains=applicant_name) |
                Q(user__last_name__icontains=applicant_name) |
                Q(user__username__icontains=applicant_name) |
                Q(user__email__icontains=applicant_name)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        # Filter by ATS score range
        ats_score_min = self.request.GET.get('ats_score_min')
        if ats_score_min:
            queryset = queryset.filter(ats_score__overall_score__gte=int(ats_score_min))
        
        ats_score_max = self.request.GET.get('ats_score_max')
        if ats_score_max:
            queryset = queryset.filter(ats_score__overall_score__lte=int(ats_score_max))
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Sorting
        sort_by = self.request.GET.get('sort_by', '-created_at')
        allowed_sort_fields = [
            'created_at', '-created_at', 
            'user__first_name', '-user__first_name', 
            'status', '-status', 
            'ats_score__overall_score', '-ats_score__overall_score'
        ]
        if sort_by in allowed_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        from django.db.models import Avg
        
        context = super().get_context_data(**kwargs)
        
        context['current_job'] = self.job
        
        # Get all applications for this job (without filters)
        all_applications = JobApplication.objects.filter(job=self.job)
        
        # Statistics
        context['total_applications'] = all_applications.count()
        context['submitted_count'] = all_applications.filter(status='submitted').count()
        context['shortlisted_count'] = all_applications.filter(status='shortlisted').count()
        context['reviewed_count'] = all_applications.filter(status='reviewed').count()
        context['interviewed_count'] = all_applications.filter(status='interviewed').count()
        context['offered_count'] = all_applications.filter(status='offered').count()
        context['hired_count'] = all_applications.filter(status='hired').count()
        context['rejected_count'] = all_applications.filter(status='rejected').count()
        context['draft_count'] = all_applications.filter(status='draft').count()
        
        # ATS Statistics
        completed_applications = all_applications.filter(
            ats_analysis_status='completed', 
            ats_score__isnull=False
        )
        context['ats_completed_count'] = completed_applications.count()
        
        avg_score = completed_applications.aggregate(Avg('ats_score__overall_score'))['ats_score__overall_score__avg']
        context['avg_ats_score'] = round(avg_score, 1) if avg_score else 0
        
        # Current filter values for template
        context['current_filters'] = {
            'applicant_name': self.request.GET.get('applicant_name', ''),
            'status': self.request.GET.get('status', 'all'),
            'ats_score_min': self.request.GET.get('ats_score_min', ''),
            'ats_score_max': self.request.GET.get('ats_score_max', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'sort_by': self.request.GET.get('sort_by', '-created_at'),
        }
        
        # Status choices for filter dropdown
        context['status_choices'] = [
            ('all', 'All Status'),
            ('submitted', 'Submitted'),
            ('reviewed', 'Reviewed'),
            ('shortlisted', 'Shortlisted'),
            ('interviewed', 'Interviewed'),
            ('offered', 'Offered'),
            ('hired', 'Hired'),
            ('rejected', 'Rejected'),
            ('draft', 'Draft'),
        ]
        
        # Check if user is job poster or just company employee
        is_job_poster = self.job.posted_by and self.job.posted_by.user == self.request.user
        context['is_job_poster'] = is_job_poster
        
        return context
    
# applications/views.py

class ResumeUploadFromApplyView(LoginRequiredMixin, CreateView):
    model = Resume
    form_class = ResumeUploadForm
    template_name = 'applications/resume_upload.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.job_id = kwargs.get('job_id')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # If this is the first resume, make it default
        if not Resume.objects.filter(user=self.request.user).exists():
            form.instance.is_default = True
        
        response = super().form_valid(form)
        messages.success(self.request, "Resume uploaded successfully!")
        
        # Redirect back to the apply page
        return redirect('apply', pk=self.job_id)
    
    def get_success_url(self):
        return reverse('apply', kwargs={'pk': self.job_id})
    
class JobApplicationDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a draft application"""
    model = JobApplication
    
    def get_queryset(self):
        # Only allow deleting applications that belong to the user
        return JobApplication.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse('my-applications')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        job_title = self.object.job.title
        self.object.delete()
        messages.success(request, f'Application for "{job_title}" has been deleted.')
        return redirect(self.get_success_url())

class UserGitHubStatsView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'applications/github_stats.html'
    context_object_name = 'profile_user'
    pk_url_kwarg = 'user_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get GitHub stats for the user
        github_stats = GitHubStats.objects.filter(user=user).first()
        context['github_stats'] = github_stats
        
        # Get user's skills for comparison
        context['user_skills'] = user.skills.all()[:10]
        
        # Get matching skills between GitHub languages and user skills
        matching_skills = []
        if github_stats and github_stats.languages:
            user_skill_names = [skill.name.lower() for skill in user.skills.all()]
            for lang, percentage in github_stats.languages.items():
                if lang.lower() in user_skill_names:
                    matching_skills.append({'name': lang, 'percentage': percentage})
        
        context['matching_skills'] = matching_skills
        
        # Check if user has GitHub link
        github_link = user.links.filter(name__iexact='github').first()
        context['github_link'] = github_link
        
        return context
    
# applications/views.py
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Avg

from .models import JobApplication, ApplicationNote, ApplicationActivity
from jobs.models import Job
from company.models import CompanyEmployee
from user.models import Notification

class UpdateApplicationStatusView(LoginRequiredMixin, View):
    """View to update application status"""
    
    def post(self, request, *args, **kwargs):
        application_id = kwargs.get('application_id')
        application = get_object_or_404(JobApplication, id=application_id)
        
        # Check permission
        if not request.user.is_staff:
            has_permission = False
            
            # Check if user is the job poster
            if application.job.posted_by and application.job.posted_by.user == request.user:
                has_permission = True
            
            # Check if user is company employee with permission
            if not has_permission and hasattr(request.user, 'employments'):
                employee = request.user.employments.filter(
                    is_active=True,
                    company=application.job.company
                ).first()
                
                if employee and employee.role.can_view_applications:
                    has_permission = True
            
            if not has_permission:
                messages.error(request, "You don't have permission to update application status.")
                return redirect('recruiter-applications', job_id=application.job.id)
        
        new_status = request.POST.get('status')
        
        if new_status in dict(application._meta.get_field('status').choices):
            old_status = application.status
            application.status = new_status
            application.save()
            
            # Create activity log
            ApplicationActivity.objects.create(
                application=application,
                action=f"Status changed from {old_status} to {new_status}",
                performed_by=request.user,
                details={'old_status': old_status, 'new_status': new_status}
            )
            
            # Create notification for the applicant
            status_display = dict(application._meta.get_field('status').choices).get(new_status, new_status)
            applicant_name = request.user.get_full_name() or request.user.username
            
            notification_message = f"Your application for '{application.job.title}' has been updated to {status_display} by {applicant_name}."
            
            Notification.objects.create(
                user=application.user,
                notification_type='system',
                message=notification_message,
                link=reverse('my-applications'),
                related_object_id=str(application.id),
                related_model='JobApplication'
            )
            
            messages.success(request, f"Application status updated to {application.get_status_display()}")
        else:
            messages.error(request, "Invalid status")
        
        return redirect('recruiter-applications', job_id=application.job.id)
    
class AddApplicationNoteView(LoginRequiredMixin, View):
    """View to add note to application"""
    
    def post(self, request, *args, **kwargs):
        application_id = kwargs.get('application_id')
        application = get_object_or_404(JobApplication, id=application_id)
        
        # Check permission
        if not request.user.is_staff:
            has_permission = False
            
            # Check if user is the job poster
            if application.job.posted_by and application.job.posted_by.user == request.user:
                has_permission = True
            
            # Check if user is company employee with permission
            if not has_permission and hasattr(request.user, 'employments'):
                employee = request.user.employments.filter(
                    is_active=True,
                    company=application.job.company
                ).first()
                
                if employee and employee.role.can_view_applications:
                    has_permission = True
            
            if not has_permission:
                messages.error(request, "You don't have permission to add notes.")
                return redirect('recruiter-applications', job_id=application.job.id)
        
        note_text = request.POST.get('note', '').strip()
        
        if note_text:
            # Create note
            note = ApplicationNote.objects.create(
                application=application,
                added_by=request.user,
                note=note_text
            )
            
            # Create activity log
            ApplicationActivity.objects.create(
                application=application,
                action="Note added",
                performed_by=request.user,
                details={'note_preview': note_text[:100]}
            )
            
            # Create notification for the applicant
            applicant_name = request.user.get_full_name() or request.user.username
            
            notification_message = f"New note added to your application for '{application.job.title}' by {applicant_name}."
            
            Notification.objects.create(
                user=application.user,
                notification_type='system',
                message=notification_message,
                link=reverse('my-applications'),
                related_object_id=str(application.id),
                related_model='JobApplication'
            )
            
            messages.success(request, "Note added successfully")
        else:
            messages.error(request, "Note cannot be empty")
        
        return redirect('recruiter-applications', job_id=application.job.id)