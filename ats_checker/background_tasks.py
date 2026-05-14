# background_tasks.py
import threading
import logging
from django.contrib.auth.models import User

from .models import ExtractedResumeContent, JobDescription, ATSScore
from user.models import Notification
from .resume_parser import AdvancedResumeParser
from .ats_scorer import AdvancedATSScorer

logger = logging.getLogger(__name__)


class ATSTaskManager:
    """Manage ATS background tasks using threading"""
    
    @staticmethod
    def run_ats_analysis_async(user_id, resume_text, jd_text, job_title, 
                                company, filename, extraction_method, word_count):
        """Run ATS analysis in background thread"""
        
        thread = threading.Thread(
            target=ATSTaskManager._process_ats_analysis,
            args=(user_id, resume_text, jd_text, job_title, company, 
                  filename, extraction_method, word_count),
            daemon=True
        )
        thread.start()
        logger.info(f"Started background ATS analysis for user {user_id} - Job: {job_title}")
        return True
    
    @staticmethod
    def _process_ats_analysis(user_id, resume_text, jd_text, job_title,
                              company, filename, extraction_method, word_count):
        """Actual processing logic running in background"""
        
        try:
            logger.info(f"Processing ATS analysis for user {user_id}")
            
            user = User.objects.get(id=user_id)
            parser = AdvancedResumeParser(use_llm=False)
            scorer = AdvancedATSScorer()
            
            # Extract structured data
            resume_structured = parser.extract_comprehensive_resume_data(resume_text)
            jd_structured = parser.extract_comprehensive_jd_data(jd_text)
            
            # Save to database
            resume = ExtractedResumeContent.objects.create(
                user=user,
                filename=filename,
                raw_text=resume_text,
                structured_json=resume_structured or {},
                extraction_method=extraction_method,
                word_count=word_count
            )
            
            jd = JobDescription.objects.create(
                user=user,
                title=job_title,
                company=company,
                raw_text=jd_text,
                formatted_jd=jd_text,
                structured_json=jd_structured or {},
                word_count=len(jd_text.split())
            )
            
            # Calculate ATS score
            score_data = scorer.calculate_comprehensive_score(
                resume.structured_json,
                jd.structured_json,
                resume.raw_text,
                jd.raw_text
            )
            
            # Default values for missing keys
            defaults = {
                'overall_score': 0.0, 'match_percentage': 0.0, 'skills_match_score': 0.0,
                'experience_match_score': 0.0, 'education_match_score': 0.0, 'keyword_match_score': 0.0,
                'formatting_score': 0.0, 'completeness_score': 0.0, 'matching_skills': [],
                'missing_skills': [], 'matching_keywords': [], 'missing_keywords': [],
                'matching_experience': [], 'missing_experience': [], 'section_suggestions': {},
                'spelling_errors': [], 'grammar_issues': [], 'style_improvements': [],
                'formatting_issues': [], 'strengths': [], 'weaknesses': [],
                'improvement_suggestions': [], 'recommendations': [], 'detailed_feedback': {}
            }
            
            for key, default_value in defaults.items():
                if key not in score_data:
                    score_data[key] = default_value
            
            # Handle improvement_plan to improvement_suggestions mapping
            if 'improvement_plan' in score_data and 'improvement_suggestions' not in score_data:
                improvement_plan = score_data['improvement_plan']
                if isinstance(improvement_plan, dict):
                    suggestions = []
                    if improvement_plan.get('critical'):
                        for item in improvement_plan['critical']:
                            suggestions.append(item.get('action', ''))
                    if improvement_plan.get('important'):
                        for item in improvement_plan['important']:
                            suggestions.append(item.get('action', ''))
                    if improvement_plan.get('quick_wins'):
                        for item in improvement_plan['quick_wins']:
                            suggestions.append(item.get('action', '') if isinstance(item, dict) else str(item))
                    score_data['improvement_suggestions'] = suggestions
                elif isinstance(improvement_plan, list):
                    score_data['improvement_suggestions'] = improvement_plan
                else:
                    score_data['improvement_suggestions'] = []
            
            # Save ATS score
            ats_score = ATSScore.objects.create(
                user=user, resume=resume, job_description=jd,
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
            
            # Create notification for user
            Notification.objects.create(
                user=user,
                notification_type="system",
                message=f"✅ ATS Analysis Complete! Your resume for '{job_title}' scored {score_data['overall_score']:.1f}%. Click to view detailed analysis.",
                link=f"/ats-checker/score/{ats_score.id}/",
                related_object_id=str(ats_score.id),
                related_model="ATSScore",
                is_read=False
            )
            
            logger.info(f"Completed ATS analysis for user {user_id} - Score: {score_data['overall_score']:.1f}%")
            
        except Exception as e:
            logger.error(f"Error in background ATS analysis for user {user_id}: {str(e)}", exc_info=True)
            try:
                user = User.objects.get(id=user_id)
                Notification.objects.create(
                    user=user,
                    notification_type="system",
                    message=f"❌ ATS Analysis Failed for '{job_title}'. Error: {str(e)[:200]}. Please try again.",
                    link="/ats-checker/dashboard/",
                    is_read=False
                )
            except:
                pass