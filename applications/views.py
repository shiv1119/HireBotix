from django.views.generic import ListView, UpdateView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from .models import (
    Resume, Education, Experience, Skill, AwardAchievement,
    ProfessionalSummary, Link, Certification, Project, JobApplication
)
from .forms import (
    ResumeForm, EducationForm, ExperienceForm, SkillForm,
    AwardAchievementForm, ProfessionalSummaryForm, LinkForm,
    CertificationForm, ProjectForm, JobApplicationForm
)
import os
import logging
logger = logging.getLogger(__name__)
# ==================== HELPER FUNCTIONS ====================

def check_profile_complete(user):
    """Helper function to check if all profile sections are complete and updated"""
    two_days_ago = timezone.now() - timedelta(days=2)
    
    # Define required sections
    required_sections = [
        ('summary', hasattr(user, 'summary') and user.summary is not None),
        ('education', user.educations.exists()),
        ('experience', user.experiences.exists()),
        ('skill', user.skills.exists()),
        ('certification', user.certifications.exists()),
        ('project', user.projects.exists())
    ]
    
    # Check if all sections exist
    all_sections_exist = all(exists for _, exists in required_sections)
    
    # If all sections exist, check if they're up to date
    if all_sections_exist:
        # Check the latest update time across all sections
        latest_updates = []
        
        if user.summary:
            latest_updates.append(user.summary.updated_at)
        if user.educations.exists():
            latest_updates.append(user.educations.order_by('-updated_at').first().updated_at)
        if user.experiences.exists():
            latest_updates.append(user.experiences.order_by('-updated_at').first().updated_at)
        if user.skills.exists():
            latest_updates.append(user.skills.order_by('-updated_at').first().updated_at)
        if user.certifications.exists():
            latest_updates.append(user.certifications.order_by('-updated_at').first().updated_at)
        if user.projects.exists():
            latest_updates.append(user.projects.order_by('-updated_at').first().updated_at)
        
        if latest_updates:
            oldest_update = min(latest_updates)
            if oldest_update < two_days_ago:
                return {
                    'complete': False,
                    'reason': 'outdated',
                    'oldest_update': oldest_update
                }
        
        return {
            'complete': True
        }
    else:
        # Find missing sections
        missing_sections = [name for name, exists in required_sections if not exists]
        return {
            'complete': False,
            'reason': 'missing',
            'missing_sections': missing_sections
        }


# ==================== MIXINS ====================

class CheckProfileCompletionMixin:
    """Mixin to check if profile sections are updated within 2 days"""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Store the next URL in session if it's a job application
            if 'next' in request.GET:
                request.session['job_application_next_url'] = request.GET.get('next')
            elif 'next' in request.POST:
                request.session['job_application_next_url'] = request.POST.get('next')
            
            # Get all profile sections with their last updated dates
            two_days_ago = timezone.now() - timedelta(days=2)
            
            sections_status = {
                'summary': {
                    'obj': getattr(request.user, 'summary', None),
                    'name': 'Professional Summary',
                    'url': self._get_summary_url(request.user),
                    'updated_at': getattr(request.user, 'summary', None).updated_at if hasattr(request.user, 'summary') and request.user.summary else None,
                    'exists': hasattr(request.user, 'summary') and request.user.summary is not None
                },
                'education': {
                    'obj': request.user.educations.order_by('-updated_at').first() if request.user.educations.exists() else None,
                    'name': 'Education',
                    'url': reverse('education-create') if not request.user.educations.exists() else reverse('education-list'),
                    'updated_at': request.user.educations.order_by('-updated_at').first().updated_at if request.user.educations.exists() else None,
                    'exists': request.user.educations.exists()
                },
                'experience': {
                    'obj': request.user.experiences.order_by('-updated_at').first() if request.user.experiences.exists() else None,
                    'name': 'Experience',
                    'url': reverse('experience-create') if not request.user.experiences.exists() else reverse('experience-list'),
                    'updated_at': request.user.experiences.order_by('-updated_at').first().updated_at if request.user.experiences.exists() else None,
                    'exists': request.user.experiences.exists()
                },
                'skill': {
                    'obj': request.user.skills.order_by('-updated_at').first() if request.user.skills.exists() else None,
                    'name': 'Skills',
                    'url': reverse('skill-create') if not request.user.skills.exists() else reverse('skill-list'),
                    'updated_at': request.user.skills.order_by('-updated_at').first().updated_at if request.user.skills.exists() else None,
                    'exists': request.user.skills.exists()
                },
                'certification': {
                    'obj': request.user.certifications.order_by('-updated_at').first() if request.user.certifications.exists() else None,
                    'name': 'Certifications',
                    'url': reverse('certification-create') if not request.user.certifications.exists() else reverse('certification-list'),
                    'updated_at': request.user.certifications.order_by('-updated_at').first().updated_at if request.user.certifications.exists() else None,
                    'exists': request.user.certifications.exists()
                },
                'project': {
                    'obj': request.user.projects.order_by('-updated_at').first() if request.user.projects.exists() else None,
                    'name': 'Projects',
                    'url': reverse('project-create') if not request.user.projects.exists() else reverse('project-list'),
                    'updated_at': request.user.projects.order_by('-updated_at').first().updated_at if request.user.projects.exists() else None,
                    'exists': request.user.projects.exists()
                }
            }
            
            incomplete_sections = []
            for key, section in sections_status.items():
                # Check if section doesn't exist OR exists but hasn't been updated in 2 days
                if not section['exists']:
                    incomplete_sections.append({
                        'name': section['name'],
                        'url': section['url'],
                        'reason': 'missing'
                    })
                elif section['updated_at'] and section['updated_at'] < two_days_ago:
                    incomplete_sections.append({
                        'name': section['name'],
                        'url': section['url'],
                        'reason': 'outdated'
                    })
            
            # Store incomplete sections in session for later use
            if incomplete_sections:
                request.session['incomplete_sections'] = incomplete_sections
            
            # If we're in a job application flow and there are incomplete sections
            if 'job_application_next_url' in request.session and incomplete_sections:
                # Store current job application URL to return after updates
                request.session['return_to_job'] = request.session.get('job_application_next_url')
                
                # Get the first incomplete section
                first_section = incomplete_sections[0]
                
                # Show appropriate message based on reason
                if first_section['reason'] == 'missing':
                    messages.warning(
                        request,
                        f"Please add your {first_section['name']} before applying. This information is required."
                    )
                else:
                    messages.warning(
                        request,
                        f"Please update your {first_section['name']} before applying. This section hasn't been updated in 2 days."
                    )
                
                # Track which sections need updating
                request.session['needs_updating'] = [s['name'] for s in incomplete_sections]
                request.session['current_updating_section'] = first_section['name']
                
                return redirect(first_section['url'])
                
        return super().dispatch(request, *args, **kwargs)
    
    def _get_summary_url(self, user):
        """Helper method to get the appropriate summary URL"""
        if hasattr(user, 'summary') and user.summary:
            return reverse('summary-update', args=[user.summary.pk])
        return reverse('summary-create')


class BaseProfileUpdateView:
    """Base class for profile update views to handle redirect tracking"""
    
    def get_success_url(self):
        # Check if we need to redirect back to job application
        if 'return_to_job' in self.request.session:
            # Get the current session data
            needs_updating = self.request.session.get('needs_updating', [])
            current_section = self.request.session.get('current_updating_section', '')
            
            # Check if we're in create or update mode
            is_create = self.request.path.endswith('/create/') or (hasattr(self, 'object') and not self.object)
            
            if is_create:
                # This was a create operation, so the section now exists
                if current_section in needs_updating:
                    needs_updating.remove(current_section)
                    self.request.session['needs_updating'] = needs_updating
            
            # If there are more sections to update, redirect to the next one
            if needs_updating:
                # Map section names to their URLs
                sections_map = {
                    'Professional Summary': 'summary-create',
                    'Education': 'education-create',
                    'Experience': 'experience-create',
                    'Skills': 'skill-create',
                    'Certifications': 'certification-create',
                    'Projects': 'project-create'
                }
                
                next_section = needs_updating[0]
                next_url = reverse(sections_map.get(next_section, 'dashboard'))
                self.request.session['current_updating_section'] = next_section
                
                messages.info(
                    self.request,
                    f"Great! Now please add your {next_section}."
                )
                return next_url
            else:
                # All sections are now complete
                job_url = self.request.session.pop('return_to_job', reverse('job-application-list'))
                self.request.session.pop('needs_updating', None)
                self.request.session.pop('current_updating_section', None)
                self.request.session.pop('incomplete_sections', None)
                
                messages.success(
                    self.request,
                    "All sections are complete! You can now submit your job application."
                )
                return job_url
        
        return super().get_success_url()


class CheckExistingApplicationMixin:
    """Mixin to check if user has already applied for a specific job"""
    
    def dispatch(self, request, *args, **kwargs):
        job_id = request.GET.get('job')
        if job_id:
            from jobs.models import Job
            
            try:
                job = Job.objects.get(id=job_id)
                
                # Check for existing application for this specific job
                existing_application = JobApplication.objects.filter(
                    user=request.user,
                    job=job
                ).first()
                
                if existing_application:
                    return render(request, 'applications/already_applied.html', {
                        'job': job,
                        'application': existing_application
                    })
            except Job.DoesNotExist:
                pass
        
        return super().dispatch(request, *args, **kwargs)


# ==================== RESUME VIEWS ====================

class ResumeListView(LoginRequiredMixin, ListView):
    model = Resume
    template_name = 'applications/resume_list.html'
    context_object_name = 'resumes'
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user).order_by('-uploaded_at')
    
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
        messages.success(self.request, 'Resume uploaded successfully!')
        return super().form_valid(form)


class ResumeUpdateView(LoginRequiredMixin, BaseProfileUpdateView, UpdateView):
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
        self.object.delete()
        messages.success(request, 'Resume deleted successfully!')
        return redirect(self.get_success_url())


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
        context['needs_updating'] = self.request.session.get('needs_updating', [])
        context['current_updating'] = self.request.session.get('current_updating_section')
        return context


class EducationCreateView(LoginRequiredMixin, BaseProfileUpdateView, CreateView):
    model = Education
    form_class = EducationForm
    template_name = 'applications/education_form.html'
    
    def get_success_url(self):
        return reverse_lazy('education-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Education added successfully!')
        return super().form_valid(form)


class EducationUpdateView(LoginRequiredMixin, BaseProfileUpdateView, UpdateView):
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


class ExperienceListView(LoginRequiredMixin, ListView):
    model = Experience
    template_name = 'applications/experience_list.html'
    context_object_name = 'experiences'
    
    def get_queryset(self):
        return Experience.objects.filter(user=self.request.user).order_by('-start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'experience'
        context['needs_updating'] = self.request.session.get('needs_updating', [])
        context['current_updating'] = self.request.session.get('current_updating_section')
        return context


class ExperienceCreateView(LoginRequiredMixin, BaseProfileUpdateView, CreateView):
    model = Experience
    form_class = ExperienceForm
    template_name = 'applications/experience_form.html'
    
    def get_success_url(self):
        return reverse_lazy('experience-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Experience added successfully!')
        return super().form_valid(form)


class ExperienceUpdateView(LoginRequiredMixin, BaseProfileUpdateView, UpdateView):
    model = Experience
    form_class = ExperienceForm
    template_name = 'applications/experience_form.html'
    
    def get_queryset(self):
        return Experience.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('experience-list')


class ExperienceDeleteView(LoginRequiredMixin, DeleteView):
    model = Experience
    template_name = 'applications/experience_confirm_delete.html'
    
    def get_queryset(self):
        return Experience.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('experience-list')


class SkillListView(LoginRequiredMixin, ListView):
    model = Skill
    template_name = 'applications/skill_list.html'
    context_object_name = 'skills'
    
    def get_queryset(self):
        return Skill.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'skill'
        context['needs_updating'] = self.request.session.get('needs_updating', [])
        context['current_updating'] = self.request.session.get('current_updating_section')
        return context


class SkillCreateView(LoginRequiredMixin, BaseProfileUpdateView, CreateView):
    model = Skill
    form_class = SkillForm
    template_name = 'applications/skill_form.html'
    
    def get_success_url(self):
        return reverse_lazy('skill-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Skill added successfully!')
        return super().form_valid(form)


class SkillUpdateView(LoginRequiredMixin, BaseProfileUpdateView, UpdateView):
    model = Skill
    form_class = SkillForm
    template_name = 'applications/skill_form.html'
    
    def get_queryset(self):
        return Skill.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('skill-list')


class SkillDeleteView(LoginRequiredMixin, DeleteView):
    model = Skill
    template_name = 'applications/skill_confirm_delete.html'
    
    def get_queryset(self):
        return Skill.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('skill-list')


class AwardAchievementListView(LoginRequiredMixin, ListView):
    model = AwardAchievement
    template_name = 'applications/award_list.html'
    context_object_name = 'awards'
    
    def get_queryset(self):
        return AwardAchievement.objects.filter(user=self.request.user).order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'award'
        return context


class AwardAchievementCreateView(LoginRequiredMixin, CreateView):
    model = AwardAchievement
    form_class = AwardAchievementForm
    template_name = 'applications/award_form.html'
    
    def get_success_url(self):
        return reverse_lazy('award-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Award added successfully!')
        return super().form_valid(form)


class AwardAchievementUpdateView(LoginRequiredMixin, UpdateView):
    model = AwardAchievement
    form_class = AwardAchievementForm
    template_name = 'applications/award_form.html'
    
    def get_queryset(self):
        return AwardAchievement.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('award-list')


class AwardAchievementDeleteView(LoginRequiredMixin, DeleteView):
    model = AwardAchievement
    template_name = 'applications/award_confirm_delete.html'
    
    def get_queryset(self):
        return AwardAchievement.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('award-list')



class ProfessionalSummaryCreateView(LoginRequiredMixin, BaseProfileUpdateView, CreateView):
    model = ProfessionalSummary
    form_class = ProfessionalSummaryForm
    template_name = 'applications/summary_form.html'
    
    def get_success_url(self):
        return reverse_lazy('profile')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Professional summary added successfully!')
        return super().form_valid(form)


class ProfessionalSummaryUpdateView(LoginRequiredMixin, BaseProfileUpdateView, UpdateView):
    model = ProfessionalSummary
    form_class = ProfessionalSummaryForm
    template_name = 'applications/summary_form.html'
    
    def get_queryset(self):
        return ProfessionalSummary.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('summary-list')


class ProfessionalSummaryDeleteView(LoginRequiredMixin, DeleteView):
    model = ProfessionalSummary
    template_name = 'applications/summary_confirm_delete.html'
    
    def get_queryset(self):
        return ProfessionalSummary.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('summary-list')

class LinkListView(LoginRequiredMixin, ListView):
    model = Link
    template_name = 'applications/link_list.html'
    context_object_name = 'links'
    
    def get_queryset(self):
        return Link.objects.filter(user=self.request.user).order_by('-created_at')
    
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
        context['needs_updating'] = self.request.session.get('needs_updating', [])
        context['current_updating'] = self.request.session.get('current_updating_section')
        return context


class CertificationCreateView(LoginRequiredMixin, BaseProfileUpdateView, CreateView):
    model = Certification
    form_class = CertificationForm
    template_name = 'applications/certification_form.html'
    
    def get_success_url(self):
        return reverse_lazy('certification-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Certification added successfully!')
        return super().form_valid(form)


class CertificationUpdateView(LoginRequiredMixin, BaseProfileUpdateView, UpdateView):
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
        context['needs_updating'] = self.request.session.get('needs_updating', [])
        context['current_updating'] = self.request.session.get('current_updating_section')
        return context


class ProjectCreateView(LoginRequiredMixin, BaseProfileUpdateView, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'applications/project_form.html'
    
    def get_success_url(self):
        return reverse_lazy('project-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Project added successfully!')
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, BaseProfileUpdateView, UpdateView):
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


# ==================== JOB APPLICATION VIEWS ====================

# ==================== JOB APPLICATION VIEWS ====================

class JobApplicationCreateView(LoginRequiredMixin, CheckExistingApplicationMixin, CreateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = 'applications/job_application_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Get job from URL parameter
        job_id = self.request.GET.get('job')
        if job_id:
            from jobs.models import Job
            job = get_object_or_404(Job, id=job_id)
            kwargs['job'] = job
        
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get job from URL parameter
        job_id = self.request.GET.get('job')
        if job_id:
            from jobs.models import Job
            context['job'] = get_object_or_404(Job, id=job_id)
        
        # Get ONLY the latest 5 resumes for the user
        context['resumes'] = Resume.objects.filter(user=self.request.user).order_by('-uploaded_at')[:5]
        context['has_resumes'] = context['resumes'].exists()
        context['total_resumes'] = Resume.objects.filter(user=self.request.user).count()
        
        # Get selected resume from POST or default to first
        if self.request.method == 'POST':
            selected_resume_id = self.request.POST.get('selected_resume')
            if selected_resume_id:
                context['selected_resume_id'] = int(selected_resume_id)
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Override post to handle both draft and submit actions"""
        self.object = None
        form = self.get_form()
        
        # Validate form
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def _run_ats_analysis(self, application):
        """Helper method to run ATS analysis if not already completed"""
        from .ats_integration import run_ats_analysis_async
        
        # Only run if ATS score doesn't exist and status is not already processing
        if not application.ats_score and application.ats_analysis_status != 'processing':
            # Check if we already have a score for this resume+job combination
            from ats_checker.models import ATSScore
            existing_score = ATSScore.objects.filter(
                user=application.user,
                resume__filename=application.resume.file.name,
                job_description__title=application.job.title
            ).first()
            
            if existing_score:
                # Use existing score
                application.ats_score = existing_score
                application.ats_analysis_status = 'completed'
                application.ats_analysis_completed_at = timezone.now()
                application.save()
                return
            
            # Run new analysis
            run_ats_analysis_async(application.id)
    
    def form_valid(self, form):
        """Handle form validation with both draft and submit options"""
        form.instance.user = self.request.user
        
        # Get the selected resume from POST data
        selected_resume_id = self.request.POST.get('selected_resume')
        
        # Validate that a resume is selected
        if not selected_resume_id:
            messages.error(self.request, 'Please select a resume to continue.')
            return self.form_invalid(form)
        
        # Set the resume
        try:
            form.instance.resume_id = selected_resume_id
        except Resume.DoesNotExist:
            messages.error(self.request, 'Selected resume does not exist.')
            return self.form_invalid(form)
        
        # Set the job
        job_id = self.request.GET.get('job')
        if job_id:
            from jobs.models import Job
            try:
                form.instance.job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                messages.error(self.request, 'Job does not exist.')
                return self.form_invalid(form)
        
        # Check for duplicate applications
        existing_application = JobApplication.objects.filter(
            user=self.request.user,
            job=form.instance.job,
            status__in=['applied', 'reviewing', 'interview', 'offered']
        ).exists()
        
        if existing_application:
            messages.error(self.request, 'You have already applied for this position.')
            return self.form_invalid(form)
        
        # Determine the action based on button clicked
        if 'save_draft' in self.request.POST:
            form.instance.status = 'draft'
            form.instance.ats_analysis_status = 'pending'
            application = form.save()
            messages.success(self.request, 'Application saved as draft. You can submit it later.')
            
            # Run ATS analysis for draft as well (so it's ready when they submit)
            self._run_ats_analysis(application)
            
            return redirect(self.get_success_url())
            
        elif 'submit_application' in self.request.POST:
            form.instance.status = 'applied'
            form.instance.ats_analysis_status = 'pending'
            application = form.save()
            messages.success(self.request, 'Job application submitted successfully! ATS analysis will be processed shortly.')
            
            # Run ATS analysis for submitted application
            self._run_ats_analysis(application)
            
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, 'Invalid action.')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        # Add resume selection error if needed
        if not self.request.POST.get('selected_resume'):
            messages.error(self.request, 'Please select a resume to continue.')
        
        # If there are other validation errors
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f'{field}: {error}')
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Return the appropriate success URL based on the action"""
        if 'save_draft' in self.request.POST:
            return reverse_lazy('job-application-list')
        return reverse_lazy('job-application-list')

class JobApplicationListView(LoginRequiredMixin, ListView):
    model = JobApplication
    template_name = 'applications/job_application_list.html'
    context_object_name = 'applications'
    
    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'job_application'
        return context


class JobApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = 'applications/job_application_form.html'
    
    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.object.job
        context['resumes'] = Resume.objects.filter(user=self.request.user).order_by('-uploaded_at')[:5]
        context['has_resumes'] = context['resumes'].exists()
        context['total_resumes'] = Resume.objects.filter(user=self.request.user).count()
        context['selected_resume_id'] = self.object.resume_id
        return context
    
    def _run_ats_analysis(self, application):
        """Helper method to run ATS analysis if not already completed"""
        from .ats_integration import run_ats_analysis_async
        
        # Only run if ATS score doesn't exist and status is not already processing
        if not application.ats_score and application.ats_analysis_status != 'processing':
            # Check if we already have a score for this resume+job combination
            from ats_checker.models import ATSScore
            existing_score = ATSScore.objects.filter(
                user=application.user,
                resume__filename=application.resume.file.name,
                job_description__title=application.job.title
            ).first()
            
            if existing_score:
                # Use existing score
                application.ats_score = existing_score
                application.ats_analysis_status = 'completed'
                application.ats_analysis_completed_at = timezone.now()
                application.save()
                return
            
            # Run new analysis
            run_ats_analysis_async(application.id)
    
    def post(self, request, *args, **kwargs):
        """Handle post request for updating applications"""
        self.object = self.get_object()
        form = self.get_form()
        
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_valid(self, form):
        """Handle form validation for updates"""
        # Update the resume if changed
        selected_resume_id = self.request.POST.get('selected_resume')
        if selected_resume_id:
            try:
                form.instance.resume_id = selected_resume_id
            except Resume.DoesNotExist:
                messages.error(self.request, 'Selected resume does not exist.')
                return self.form_invalid(form)
        
        # Determine the action
        if 'save_draft' in self.request.POST:
            form.instance.status = 'draft'
            application = form.save()
            messages.success(self.request, 'Draft updated successfully.')
            
            # Run ATS analysis if resume changed or no score exists
            if 'selected_resume' in self.request.POST or not application.ats_score:
                self._run_ats_analysis(application)
            
            return redirect(self.get_success_url())
            
        elif 'submit_application' in self.request.POST:
            form.instance.status = 'applied'
            application = form.save()
            messages.success(self.request, 'Application submitted successfully! ATS analysis will be processed.')
            
            # Always run ATS analysis on submit
            self._run_ats_analysis(application)
            
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, 'Invalid action.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('job-application-list')


class JobApplicationDeleteView(LoginRequiredMixin, DeleteView):
    model = JobApplication
    template_name = 'applications/job_application_confirm_delete.html'
    
    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('job-application-list')
    


from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
# from django.db.models import Count, Q, F
# from django.core.paginator import Paginator
# from django.shortcuts import get_object_or_404
from .models import JobApplication
# from datetime import datetime, timedelta
# from django.utils import timezone
from jobs.models import Job
from django.db.models import Avg

class RecruiterApplicationsListView(LoginRequiredMixin, ListView):
    model = JobApplication
    template_name = 'applications/recruiter_applications.html'
    context_object_name = 'applications'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        # Get the job ID from URL and verify it belongs to the recruiter
        self.job = get_object_or_404(Job, id=kwargs['job_id'], recruiter=request.user)
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Get only applications for this specific job
        # Order by ATS score (highest first), then by created date (newest first)
        return JobApplication.objects.filter(
            job=self.job
        ).select_related(
            'user', 'job', 'resume', 'ats_score'
        ).order_by(
            '-ats_score__overall_score',  # Highest ATS score first
            '-created_at'  # Then newest applications
        )
    
    def trigger_missing_ats_analyses(self):
        """Check for applications without ATS scores and trigger background tasks"""
        from .ats_integration import run_ats_analysis_async
        
        # Find applications for this job that need ATS analysis
        applications_needing_ats = JobApplication.objects.filter(
            job=self.job,
            ats_score__isnull=True,
            ats_analysis_status__in=['pending', 'failed', None],
            status__in=['applied', 'draft']
        ).exclude(
            ats_analysis_status='processing'
        )
        
        triggered_count = 0
        for application in applications_needing_ats:
            # Update status to processing to avoid duplicate triggers
            application.ats_analysis_status = 'processing'
            application.ats_analysis_started_at = timezone.now()
            application.save(update_fields=['ats_analysis_status', 'ats_analysis_started_at'])
            
            # Trigger background analysis
            run_ats_analysis_async(application.id)
            triggered_count += 1
            logger.info(f"Triggered ATS analysis for application {application.id} - Job: {application.job.title}")
        
        if triggered_count > 0:
            logger.info(f"Triggered ATS analysis for {triggered_count} applications for job: {self.job.title}")
        
        return triggered_count
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the current job
        context['current_job'] = self.job
        
        # Get all applications for this job (for statistics)
        all_applications = JobApplication.objects.filter(job=self.job)
        
        context['total_applications'] = all_applications.count()
        context['applied_count'] = all_applications.filter(status='applied').count()
        context['draft_count'] = all_applications.filter(status='draft').count()
        context['cancelled_count'] = all_applications.filter(status='cancelled').count()
        
        # ATS Statistics for this job
        context['ats_completed_count'] = all_applications.filter(
            ats_analysis_status='completed', 
            ats_score__isnull=False
        ).count()
        
        context['ats_pending_count'] = all_applications.filter(
            ats_analysis_status='pending'
        ).count()
        
        context['ats_processing_count'] = all_applications.filter(
            ats_analysis_status='processing'
        ).count()
        
        context['ats_failed_count'] = all_applications.filter(
            ats_analysis_status='failed'
        ).count()
        
        # Calculate average score for completed analyses
        completed_ats = all_applications.filter(
            ats_analysis_status='completed', 
            ats_score__isnull=False
        )
        avg_score = completed_ats.aggregate(Avg('ats_score__overall_score'))['ats_score__overall_score__avg']
        context['avg_ats_score'] = round(avg_score, 1) if avg_score else 0
        
        # Get top 3 highest scoring applications for the job
        top_applications = all_applications.filter(
            ats_analysis_status='completed',
            ats_score__isnull=False
        ).order_by('-ats_score__overall_score')[:3]
        
        top_scores = []
        for app in top_applications:
            top_scores.append({
                'name': app.user.get_full_name() or app.user.username,
                'score': app.ats_score.overall_score,
                'application_id': app.id
            })
        context['top_ats_scores'] = top_scores
        
        # Trigger missing ATS analyses
        self.trigger_missing_ats_analyses()
        
        return context