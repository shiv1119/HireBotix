from django.views.generic import CreateView, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Job
from .forms import JobForm
from django.views.generic import DetailView
from django.db.models import Q, Value, IntegerField
from django.db.models.functions import Concat
from django.utils import timezone

class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/create_job.html'
    login_url = 'login'

    def form_valid(self, form):
        form.instance.recruiter = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('job_detail', kwargs={'job_id': self.object.id})
    
class JobListView(ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        queryset = Job.objects.filter(is_active=True)

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

class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'
    pk_url_kwarg = 'job_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        
        # Check if user has already applied
        has_applied = False
        if self.request.user.is_authenticated:
            has_applied = job.applications.filter(
                user=self.request.user,
                status__in=['applied', 'reviewing', 'interview', 'offered']
            ).exists()
        
        # Get similar jobs
        similar_jobs = Job.objects.exclude(pk=job.pk).filter(
            Q(title__icontains=job.title) |
            Q(skills_required__icontains=job.skills_required) |
            Q(location__icontains=job.location)
        ).order_by('-created_at')[:10]
        
        # Get recent jobs
        recent_jobs = Job.objects.exclude(pk=job.pk).order_by('-created_at')[:10]
        
        context['similar_jobs'] = similar_jobs
        context['recent_jobs'] = recent_jobs
        context['has_applied'] = has_applied
        
        return context
    
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Job

class UserJobsListView(LoginRequiredMixin, ListView):
    """
    View to list all jobs posted by a specific user
    URL: /jobs/user/<int:user_id>/
    """
    model = Job
    template_name = 'jobs/user_jobs.html'
    context_object_name = 'jobs'
    paginate_by = 10
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        # Get the user or return 404
        user = get_object_or_404(User, id=user_id)
        
        # Filter jobs by this user only - NO filters
        queryset = Job.objects.filter(recruiter=user, is_active=True).order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id')
        context['profile_user'] = get_object_or_404(User, id=user_id)
        context['is_owner'] = self.request.user.id == user_id
        return context