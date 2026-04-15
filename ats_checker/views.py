# views.py - Simplified version
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
import logging

from .models import ExtractedResumeContent, JobDescription, ATSScore
from .resume_parser import AdvancedResumeParser, parse_uploaded_file
from .ats_scorer import AdvancedATSScorer

logger = logging.getLogger(__name__)


class ATSDashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard with resume upload and JD input"""
    template_name = 'ats_checker/dashboard.html'
    
    def post(self, request, *args, **kwargs):
        # Handle resume upload
        if not request.FILES.get('resume'):
            messages.error(request, 'Please upload a resume file')
            return redirect('dashboard')
        
        # Handle JD form fields
        jd_text = request.POST.get('jd_text', '')
        job_title = request.POST.get('title', '')
        company = request.POST.get('company', '')
        
        if not jd_text or not job_title:
            messages.error(request, 'Please provide both job title and description')
            return redirect('dashboard')
        
        # Process resume
        uploaded_file = request.FILES['resume']
        result = parse_uploaded_file(uploaded_file)
        
        if not result['success']:
            messages.error(request, f'Error processing resume: {result["error"]}')
            return redirect('dashboard')
        
        try:
            parser = AdvancedResumeParser(use_llm=False)
            
            # Extract and save resume
            resume_structured = parser.extract_comprehensive_resume_data(result['text'])
            resume = ExtractedResumeContent.objects.create(
                user=request.user,
                filename=uploaded_file.name,
                raw_text=result['text'],
                structured_json=resume_structured,
                extraction_method=result['method'],
                word_count=len(result['text'].split())
            )
            
            # Extract and save job description
            jd_structured = parser.extract_comprehensive_jd_data(jd_text)
            jd = JobDescription.objects.create(
                user=request.user,
                title=job_title,
                company=company,
                raw_text=jd_text,
                formatted_jd=jd_text,
                structured_json=jd_structured,
                word_count=len(jd_text.split())
            )
            
            # Calculate ATS score
            scorer = AdvancedATSScorer()
            score_data = scorer.calculate_comprehensive_score(
                resume.structured_json,
                jd.structured_json,
                resume.raw_text,
                jd.raw_text
            )
            
            # Save ATS score
            ats_score = ATSScore.objects.create(
                user=request.user,
                resume=resume,
                job_description=jd,
                overall_score=score_data['overall_score'],
                match_percentage=score_data['match_percentage'],
                skills_match_score=score_data['skills_match_score'],
                experience_match_score=score_data['experience_match_score'],
                education_match_score=score_data['education_match_score'],
                keyword_match_score=score_data['keyword_match_score'],
                formatting_score=score_data['formatting_score'],
                completeness_score=score_data['completeness_score'],
                matching_skills=score_data['matching_skills'],
                missing_skills=score_data['missing_skills'],
                matching_keywords=score_data['matching_keywords'],
                missing_keywords=score_data['missing_keywords'],
                matching_experience=score_data['matching_experience'],
                missing_experience=score_data['missing_experience'],
                section_suggestions=score_data['section_suggestions'],
                spelling_errors=score_data['spelling_errors'],
                grammar_issues=score_data['grammar_issues'],
                style_improvements=score_data['style_improvements'],
                formatting_issues=score_data['formatting_issues'],
                strengths=score_data['strengths'],
                weaknesses=score_data['weaknesses'],
                improvement_suggestions=score_data['improvement_suggestions'],
                recommendations=score_data['recommendations'],
                detailed_feedback=score_data['detailed_feedback']
            )
            
            messages.success(request, f'ATS Score: {score_data["overall_score"]:.1f}%')
            return redirect('score_detail', pk=ats_score.id)
            
        except Exception as e:
            logger.error(f"Error processing: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
            return redirect('dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_scores'] = ATSScore.objects.filter(
            user=self.request.user
        ).select_related('resume', 'job_description')[:5]
        return context


class ScoreDetailView(LoginRequiredMixin, DetailView):
    """Display detailed ATS score analysis"""
    model = ATSScore
    template_name = 'ats_checker/score_detail.html'
    context_object_name = 'score'
    
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['score_metrics'] = [
            {'label': 'Skills Match', 'score': self.object.skills_match_score, 'color': '#3B82F6'},
            {'label': 'Experience Match', 'score': self.object.experience_match_score, 'color': '#10B981'},
            {'label': 'Education Match', 'score': self.object.education_match_score, 'color': '#F59E0B'},
            {'label': 'Keyword Match', 'score': self.object.keyword_match_score, 'color': '#8B5CF6'},
            {'label': 'Formatting', 'score': self.object.formatting_score, 'color': '#EC4899'},
            {'label': 'Completeness', 'score': self.object.completeness_score, 'color': '#6366F1'},
        ]
        return context