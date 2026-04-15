# applications/ats_integration.py
import threading
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class ATSIntegrationService:
    """Handle ATS analysis for job applications"""
    
    @staticmethod
    def analyze_application_ats(application_id):
        """Run ATS analysis for a job application"""
        from .models import JobApplication
        from ats_checker.models import ExtractedResumeContent, JobDescription, ATSScore
        from ats_checker.resume_parser import AdvancedResumeParser, parse_uploaded_file
        from ats_checker.ats_scorer import AdvancedATSScorer
        
        try:
            application = JobApplication.objects.get(id=application_id)
            
            # Check if analysis already completed
            if application.ats_score and application.ats_analysis_status == 'completed':
                logger.info(f"ATS analysis already completed for application {application_id}")
                return True
            
            # Update status to processing
            application.ats_analysis_status = 'processing'
            application.ats_analysis_started_at = timezone.now()
            application.save()
            
            # Check if ATS score already exists for this resume+job combination
            existing_ats = ATSScore.objects.filter(
                user=application.user,
                resume__filename=application.resume.file.name,
                job_description__title=application.job.title
            ).first()
            
            if existing_ats:
                # Use existing ATS score
                application.ats_score = existing_ats
                application.ats_analysis_status = 'completed'
                application.ats_analysis_completed_at = timezone.now()
                application.save()
                logger.info(f"Existing ATS score used for application {application_id}")
                return True
            
            # Extract resume content
            resume_file = application.resume.file
            resume_file.open('rb')
            file_content = resume_file.read()
            resume_file.close()
            
            # Create a temporary file-like object
            from django.core.files.uploadedfile import SimpleUploadedFile
            temp_file = SimpleUploadedFile(
                application.resume.file.name,
                file_content,
                content_type='application/pdf'
            )
            
            # Parse resume
            parse_result = parse_uploaded_file(temp_file)
            
            if not parse_result['success']:
                raise Exception(f"Resume parsing failed: {parse_result['error']}")
            
            # Extract resume data
            parser = AdvancedResumeParser(use_llm=False)
            resume_structured = parser.extract_comprehensive_resume_data(parse_result['text'])
            
            # Save extracted resume
            extracted_resume = ExtractedResumeContent.objects.create(
                user=application.user,
                filename=application.resume.file.name,
                raw_text=parse_result['text'],
                structured_json=resume_structured,
                extraction_method=parse_result['method'],
                word_count=len(parse_result['text'].split()),
                page_count=1
            )
            
            # Create job description text from Job model
            jd_text = f"""
            Title: {application.job.title}
            Company: {application.job.company_name}
            
            Description:
            {application.job.description}
            
            Responsibilities:
            {application.job.responsibilities}
            
            Requirements:
            {application.job.requirements}
            
            Skills Required: {application.job.skills_required}
            """
            
            # Extract JD data
            jd_structured = parser.extract_comprehensive_jd_data(jd_text)
            
            # Save job description
            job_desc = JobDescription.objects.create(
                user=application.job.recruiter,
                title=application.job.title,
                company=application.job.company_name,
                raw_text=jd_text,
                formatted_jd=jd_text,
                structured_json=jd_structured,
                word_count=len(jd_text.split())
            )
            
            # Calculate ATS score
            scorer = AdvancedATSScorer()
            score_data = scorer.calculate_comprehensive_score(
                resume_structured,
                jd_structured,
                parse_result['text'],
                jd_text
            )
            
            # Save ATS score
            ats_score = ATSScore.objects.create(
                user=application.user,
                resume=extracted_resume,
                job_description=job_desc,
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
            
            # Update application with ATS score
            application.ats_score = ats_score
            application.ats_analysis_status = 'completed'
            application.ats_analysis_completed_at = timezone.now()
            application.save()
            
            logger.info(f"ATS analysis completed for application {application_id} with score {ats_score.overall_score}")
            return True
            
        except Exception as e:
            logger.error(f"ATS analysis failed for application {application_id}: {str(e)}")
            try:
                application = JobApplication.objects.get(id=application_id)
                application.ats_analysis_status = 'failed'
                application.save()
            except:
                pass
            return False


def run_ats_analysis_async(application_id):
    """Run ATS analysis in background thread"""
    thread = threading.Thread(target=ATSIntegrationService.analyze_application_ats, args=(application_id,))
    thread.daemon = True
    thread.start()