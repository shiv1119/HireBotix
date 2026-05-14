# views.py
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
import logging
from django.urls import reverse
from urllib.parse import urlencode
from .models import ExtractedResumeContent, JobDescription, ATSScore
from user.models import Notification
from .resume_parser import parse_uploaded_file
from .background_tasks import ATSTaskManager

logger = logging.getLogger(__name__)


class ATSDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ats_checker/dashboard.html'
    
    def post(self, request, *args, **kwargs):
        # Validation
        if not request.FILES.get('resume'):
            messages.error(request, 'Please upload a resume file')
            return redirect('dashboard')
        
        jd_text = request.POST.get('jd_text', '')
        job_title = request.POST.get('title', '')
        company = request.POST.get('company', '')
        
        if not jd_text or not job_title:
            messages.error(request, 'Please provide both job title and description')
            return redirect('dashboard')
        
        # Extract text from uploaded file
        uploaded_file = request.FILES['resume']
        result = parse_uploaded_file(uploaded_file)
        
        if not result['success']:
            messages.error(request, f'Error processing resume: {result["error"]}')
            return redirect('dashboard')
        
        try:
            # Start background processing (non-blocking)
            ATSTaskManager.run_ats_analysis_async(
                user_id=request.user.id,
                resume_text=result['text'],
                jd_text=jd_text,
                job_title=job_title,
                company=company,
                filename=uploaded_file.name,
                extraction_method=result['method'],
                word_count=len(result['text'].split())
            )
            
            # Simple message - no JS, no API
            messages.success(
                request, 
                f'Analysis started for "{job_title}"! You will be notified when ready. Check your notifications and visit the ATS results page to see your detailed analysis.'
            )
            
            base_url = reverse('dashboard')
            query_string = urlencode({'show_modal': 'true', 'job_title': job_title})
            return redirect(f'{base_url}?{query_string}')
            
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            messages.error(request, f'Error: {str(e)}')
            return redirect('dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_scores'] = ATSScore.objects.filter(
            user=self.request.user
        ).select_related('resume', 'job_description').order_by('-created_at')[:5]
        
        # Pass notifications to template for display
        context['notifications'] = Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:10]
        
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user, is_read=False
        ).count()
        
        return context


class ScoreDetailView(LoginRequiredMixin, DetailView):
    model = ATSScore
    template_name = 'ats_checker/score_detail.html'
    context_object_name = 'score'
    pk_url_kwarg = 'pk'
    
    def get_queryset(self):
        # Return all scores, no permission filtering
        return ATSScore.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Mark notification as read only if the notification belongs to the current user
        # and is related to this score
        Notification.objects.filter(
            user=self.request.user,
            related_object_id=str(self.object.id),
            related_model="ATSScore",
            is_read=False
        ).update(is_read=True)
        
        context['score_metrics'] = [
            {'label': 'Skills Match', 'score': self.object.skills_match_score, 'color': '#3B82F6'},
            {'label': 'Experience Match', 'score': self.object.experience_match_score, 'color': '#10B981'},
            {'label': 'Education Match', 'score': self.object.education_match_score, 'color': '#F59E0B'},
            {'label': 'Keyword Match', 'score': self.object.keyword_match_score, 'color': '#8B5CF6'},
            {'label': 'Formatting', 'score': self.object.formatting_score, 'color': '#EC4899'},
            {'label': 'Completeness', 'score': self.object.completeness_score, 'color': '#6366F1'},
        ]
        
        return context
    
from django.views.generic import ListView
class ATSResultsView(LoginRequiredMixin, ListView):
    """Display user's top 10 latest ATS analyses"""
    model = ATSScore
    template_name = 'ats_checker/ats-results.html'
    context_object_name = 'scores'
    
    def get_queryset(self):
        """Get user's top 10 latest scores"""
        return ATSScore.objects.filter(
            user=self.request.user
        ).select_related('resume', 'job_description').order_by('-created_at')[:10]