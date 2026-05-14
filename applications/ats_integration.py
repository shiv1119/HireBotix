# applications/ats_integration.py
import threading
from django.utils import timezone
import logging
from .models import *
logger = logging.getLogger(__name__)
try:
    from .github_service import GitHubService, GitHubStatsUpdater
except ImportError:
    GitHubService = None
    GitHubStatsUpdater = None
    logger.warning("GitHub service not available")

class ATSIntegrationService:
    """Handle ATS analysis for job applications"""
    
    @staticmethod
    def extract_and_save_resume_data(user, structured_json):
        """
        Extract data from structured JSON and save to respective models
        Only inserts if data doesn't already exist
        """
        results = {
            'skills_added': 0,
            'experiences_added': 0,
            'educations_added': 0,
            'certifications_added': 0,
            'projects_added': 0,
            'links_added': 0,
            'github_link_found': False,
            'github_username': None,
            'summary_added': False,
            'errors': []
        }
        
        try:
            # 1. Extract and save Professional Summary
            try:
                if structured_json.get('personal_info', {}).get('summary'):
                    summary_text = structured_json['personal_info']['summary']
                    if not hasattr(user, 'summary') or not user.summary:
                        ProfessionalSummary.objects.create(
                            user=user,
                            summary=summary_text
                        )
                        results['summary_added'] = True
                        logger.info(f"Added professional summary for user {user.username}")
            except Exception as e:
                error_msg = f"Failed to save professional summary: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # 2. Extract and save Skills
            try:
                skills_data = structured_json.get('skills', {})
                all_skills = []
                
                if skills_data.get('technical'):
                    all_skills.extend(skills_data['technical'])
                if skills_data.get('soft'):
                    all_skills.extend(skills_data['soft'])
                if skills_data.get('tools'):
                    all_skills.extend(skills_data['tools'])
                if skills_data.get('languages'):
                    all_skills.extend(skills_data['languages'])
                
                existing_skill_names = set(Skill.objects.filter(user=user).values_list('name', flat=True))
                
                for skill_name in all_skills:
                    if skill_name not in existing_skill_names:
                        Skill.objects.create(user=user, name=skill_name)
                        results['skills_added'] += 1
                
                if results['skills_added'] > 0:
                    logger.info(f"Added {results['skills_added']} skills for user {user.username}")
            except Exception as e:
                error_msg = f"Failed to save skills: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # 3. Extract and save Work Experience
            try:
                experiences_data = structured_json.get('experience', [])
                
                for exp in experiences_data:
                    existing_exp = Experience.objects.filter(
                        user=user,
                        job_title=exp.get('title', ''),
                        company=exp.get('company', '')
                    ).first()
                    
                    if not existing_exp:
                        start_date = None
                        end_date = None
                        
                        if exp.get('start_date'):
                            try:
                                from datetime import datetime
                                start_date = datetime.strptime(exp['start_date'], '%b %Y').date()
                            except:
                                pass
                        
                        if exp.get('end_date') and exp['end_date'] != 'Present':
                            try:
                                end_date = datetime.strptime(exp['end_date'], '%b %Y').date()
                            except:
                                pass
                        
                        description = ""
                        if exp.get('responsibilities'):
                            description += "Responsibilities:\n" + "\n".join(f"• {resp}" for resp in exp['responsibilities'])
                        if exp.get('achievements'):
                            if description:
                                description += "\n\n"
                            description += "Achievements:\n" + "\n".join(f"• {ach}" for ach in exp['achievements'])
                        
                        Experience.objects.create(
                            user=user,
                            job_title=exp.get('title', ''),
                            company=exp.get('company', ''),
                            start_date=start_date or timezone.now().date(),
                            end_date=end_date,
                            description=description
                        )
                        results['experiences_added'] += 1
                
                if results['experiences_added'] > 0:
                    logger.info(f"Added {results['experiences_added']} experiences for user {user.username}")
            except Exception as e:
                error_msg = f"Failed to save experiences: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # 4. Extract and save Education
            try:
                education_data = structured_json.get('education', [])
                
                for edu in education_data:
                    existing_edu = Education.objects.filter(
                        user=user,
                        degree=edu.get('degree', ''),
                        institution=edu.get('institution', '')
                    ).first()
                    
                    if not existing_edu:
                        start_year = None
                        end_year = None
                        
                        if edu.get('start_date'):
                            try:
                                start_year = int(edu['start_date'][:4]) if len(edu['start_date']) >= 4 else None
                            except:
                                pass
                        
                        if edu.get('end_date'):
                            try:
                                end_year = int(edu['end_date'][:4]) if len(edu['end_date']) >= 4 else None
                            except:
                                pass
                        
                        Education.objects.create(
                            user=user,
                            degree=edu.get('degree', ''),
                            institution=edu.get('institution', ''),
                            start_year=start_year or 2000,
                            end_year=end_year,
                            grade=edu.get('cgpa', '')
                        )
                        results['educations_added'] += 1
                
                if results['educations_added'] > 0:
                    logger.info(f"Added {results['educations_added']} education records for user {user.username}")
            except Exception as e:
                error_msg = f"Failed to save education: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # 5. Extract and save Certifications & Achievements
            try:
                achievements_data = structured_json.get('achievements', [])
                
                for achievement in achievements_data:
                    existing_cert = Certification.objects.filter(
                        user=user,
                        name=achievement.get('title', '')
                    ).first()
                    
                    if not existing_cert:
                        cert_date = None
                        if achievement.get('date'):
                            try:
                                from datetime import datetime
                                cert_date = datetime.strptime(achievement['date'], '%b %Y').date()
                            except:
                                pass
                        
                        Certification.objects.create(
                            user=user,
                            name=achievement.get('title', ''),
                            organization=achievement.get('issuer', ''),
                            date=cert_date
                        )
                        results['certifications_added'] += 1
                
                if results['certifications_added'] > 0:
                    logger.info(f"Added {results['certifications_added']} certifications for user {user.username}")
            except Exception as e:
                error_msg = f"Failed to save certifications: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # 6. Extract and save Projects
            try:
                projects_data = structured_json.get('projects', [])
                
                for project in projects_data:
                    existing_project = Project.objects.filter(
                        user=user,
                        title=project.get('name', '')
                    ).first()
                    
                    if not existing_project:
                        github_link = None
                        if project.get('github'):
                            github_link = project['github']
                        
                        Project.objects.create(
                            user=user,
                            title=project.get('name', ''),
                            description=project.get('description', ''),
                            github_link=github_link
                        )
                        results['projects_added'] += 1
                
                if results['projects_added'] > 0:
                    logger.info(f"Added {results['projects_added']} projects for user {user.username}")
            except Exception as e:
                error_msg = f"Failed to save projects: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # 7. Extract and save Links (GitHub, LinkedIn, etc.)
            try:
                personal_info = structured_json.get('personal_info', {})
                links_to_add = []
                
                if personal_info.get('github'):
                    github_url = personal_info['github']
                    # Ensure it's a full URL
                    if not github_url.startswith('http'):
                        github_url = f"https://github.com/{github_url}"
                    links_to_add.append(('GitHub', github_url))
                    results['github_link_found'] = True
                    results['github_username'] = GitHubService.extract_username(github_url) if 'GitHubService' in globals() else None
                
                if personal_info.get('linkedin'):
                    links_to_add.append(('LinkedIn', personal_info['linkedin']))
                
                existing_links = set(Link.objects.filter(user=user).values_list('url', flat=True))
                
                for link_name, link_url in links_to_add:
                    if link_url and link_url not in existing_links:
                        Link.objects.create(
                            user=user,
                            name=link_name,
                            url=link_url
                        )
                        results['links_added'] += 1
                
                if results['links_added'] > 0:
                    logger.info(f"Added {results['links_added']} links for user {user.username}")
            except Exception as e:
                error_msg = f"Failed to save links: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error in data extraction: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        # Log summary
        if results['errors']:
            logger.warning(f"Data extraction completed with {len(results['errors'])} errors for user {user.username}")
        else:
            logger.info(f"Data extraction completed successfully for user {user.username}")
        
        return results
    
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
            
            # Check if ATS score already exists
            existing_ats = ATSScore.objects.filter(
                user=application.user,
                resume__filename=application.resume.file.name,
                job_description__title=application.job.title
            ).first()
            
            if existing_ats:
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
            
            # Extract and save data to respective models
            extract_results = None
            try:
                extract_results = ATSIntegrationService.extract_and_save_resume_data(
                    application.user, 
                    resume_structured
                )
                logger.info(f"Data extraction results for user {application.user.username}: {extract_results}")
            except Exception as e:
                logger.error(f"Critical error in data extraction (continuing with ATS): {str(e)}")
            
            # Get company name
            company_name = application.job.company.name if application.job.company else "Unknown Company"
            
            # Create job description text
            jd_text = f"""
            Title: {application.job.title}
            Company: {company_name}
            
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
            
            # Get posted by user
            posted_by_user = None
            if application.job.posted_by and application.job.posted_by.user:
                posted_by_user = application.job.posted_by.user
            elif application.job.company and application.job.company.employees.filter(role__name='company_admin').first():
                posted_by_user = application.job.company.employees.filter(role__name='company_admin').first().user
            
            # Save job description
            job_desc = JobDescription.objects.create(
                user=posted_by_user,
                title=application.job.title,
                company=company_name,
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
                overall_score=score_data.get('overall_score', 0),
                match_percentage=score_data.get('match_percentage', 0),
                skills_match_score=score_data.get('skills_match_score', 0),
                experience_match_score=score_data.get('experience_match_score', 0),
                education_match_score=score_data.get('education_match_score', 0),
                keyword_match_score=score_data.get('keyword_match_score', 0),
                formatting_score=score_data.get('formatting_score', 0),
                completeness_score=score_data.get('completeness_score', 0),
                matching_skills=score_data.get('matching_skills', []),
                missing_skills=score_data.get('missing_skills', []),
                matching_keywords=score_data.get('matching_keywords', []),
                missing_keywords=score_data.get('missing_keywords', []),
                matching_experience=score_data.get('matching_experience', []),
                missing_experience=score_data.get('missing_experience', []),
                section_suggestions=score_data.get('section_suggestions', {}),
                spelling_errors=score_data.get('spelling_errors', []),
                grammar_issues=score_data.get('grammar_issues', []),
                style_improvements=score_data.get('style_improvements', []),
                formatting_issues=score_data.get('formatting_issues', []),
                strengths=score_data.get('strengths', []),
                weaknesses=score_data.get('weaknesses', []),
                improvement_suggestions=score_data.get('improvement_suggestions', []),
                recommendations=score_data.get('recommendations', []),
                detailed_feedback=score_data.get('detailed_feedback', '')
            )
            
            # Update application with ATS score
            application.ats_score = ats_score
            application.ats_analysis_status = 'completed'
            application.ats_analysis_completed_at = timezone.now()
            application.save()
            
            logger.info(f"ATS analysis completed for application {application_id} with score {ats_score.overall_score}")
            
            # TRIGGER GITHUB STATS FETCHING AFTER ATS COMPLETES
            if extract_results and extract_results.get('github_link_found'):
                try:
                    from applications.github_service import GitHubStatsUpdater
                    from applications.models import GitHubStats
                    
                    # Check if we already have fresh stats
                    needs_update = GitHubStatsUpdater.needs_update(application.user)
                    
                    if needs_update:
                        logger.info(f"GitHub link found for user {application.user.username}. Fetching GitHub stats (needs update)...")
                        GitHubStatsUpdater.update_stats_async(application.user)
                    else:
                        logger.info(f"Skipping GitHub stats fetch for {application.user.username} - already fresh")
                        
                except Exception as e:
                    logger.error(f"Failed to trigger GitHub stats fetch: {str(e)}")
            
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