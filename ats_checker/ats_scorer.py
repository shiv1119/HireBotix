# ats_scorer.py
import re
from typing import Dict, List, Any, Tuple
from difflib import SequenceMatcher
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json
import logging
from collections import Counter

logger = logging.getLogger(__name__)

class AdvancedATSScorer:

    def __init__(self, ollama_url="http://localhost:11434", model="gemma:2b"):
        self.ollama_url = ollama_url
        self.model = model
        self.weights = {
            'skills': 0.40,
            'experience': 0.25,
            'education': 0.10,
            'keywords': 0.15,
            'formatting': 0.05,
            'completeness': 0.05
        }
    
    def calculate_comprehensive_score(self, resume_data: Dict, jd_data: Dict, 
                                     resume_text: str, jd_text: str) -> Dict[str, Any]:        
        logger.info("=" * 60)
        logger.info("Starting ATS Score Calculation")
        logger.info("=" * 60)
        
        # Calculate all component scores
        skills_result = self._calculate_skills_match(resume_data, jd_data)
        logger.info(f"Skills Match Score: {skills_result['score'] * 100:.1f}%")
        logger.info(f"Matching Skills: {skills_result['matching']}")
        logger.info(f"Missing Skills: {skills_result['missing']}")
        
        experience_result = self._calculate_experience_match(resume_data, jd_data)
        logger.info(f"Experience Match Score: {experience_result['score'] * 100:.1f}%")
        
        education_result = self._calculate_education_match(resume_data, jd_data)
        logger.info(f"Education Match Score: {education_result['score'] * 100:.1f}%")
        
        keywords_result = self._calculate_keywords_match(resume_text, jd_data, jd_text)
        logger.info(f"Keyword Match Score: {keywords_result['score'] * 100:.1f}%")
        
        formatting_result = self._calculate_formatting_score(resume_text)
        completeness_result = self._calculate_completeness_score(resume_data)
        
        # Calculate weighted overall score
        overall_score = (
            self.weights['skills'] * skills_result['score'] +
            self.weights['experience'] * experience_result['score'] +
            self.weights['education'] * education_result['score'] +
            self.weights['keywords'] * keywords_result['score'] +
            self.weights['formatting'] * formatting_result['score'] +
            self.weights['completeness'] * completeness_result['score']
        ) * 100
        
        logger.info(f"Overall ATS Score: {overall_score:.1f}%")
        logger.info("=" * 60)
        
        # Generate AI-powered suggestions
        section_suggestions = self._generate_section_suggestions(resume_data, jd_data)
        spelling_errors = self._check_spelling_errors(resume_text)
        grammar_issues = self._check_grammar_issues(resume_text)
        style_improvements = self._analyze_style_improvements(resume_text, jd_data)
        formatting_issues = self._analyze_formatting_issues(resume_text)
        
        # Identify strengths and weaknesses
        strengths, weaknesses = self._identify_strengths_weaknesses(
            skills_result, experience_result, education_result, keywords_result
        )
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            skills_result, experience_result, education_result, keywords_result,
            formatting_result, completeness_result, spelling_errors, grammar_issues
        )
        
        # Generate comprehensive recommendations
        recommendations = self._generate_comprehensive_recommendations(
            improvement_suggestions, strengths, weaknesses
        )
        
        # Generate detailed feedback
        detailed_feedback = self._generate_detailed_feedback(
            overall_score, skills_result, experience_result, education_result,
            keywords_result, strengths, weaknesses, recommendations
        )
        
        return {
            'overall_score': round(overall_score, 2),
            'match_percentage': round(overall_score, 2),
            'skills_match_score': round(skills_result['score'] * 100, 2),
            'experience_match_score': round(experience_result['score'] * 100, 2),
            'education_match_score': round(education_result['score'] * 100, 2),
            'keyword_match_score': round(keywords_result['score'] * 100, 2),
            'formatting_score': round(formatting_result['score'] * 100, 2),
            'completeness_score': round(completeness_result['score'] * 100, 2),
            'matching_skills': skills_result['matching'],
            'missing_skills': skills_result['missing'],
            'matching_keywords': keywords_result['matching'],
            'missing_keywords': keywords_result['missing'],
            'matching_experience': experience_result['matching'],
            'missing_experience': experience_result['missing'],
            'section_suggestions': section_suggestions,
            'spelling_errors': spelling_errors,
            'grammar_issues': grammar_issues,
            'style_improvements': style_improvements,
            'formatting_issues': formatting_issues,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'improvement_suggestions': improvement_suggestions,
            'recommendations': recommendations,
            'detailed_feedback': detailed_feedback
        }
    
    def _extract_skills_from_text(self, text: str) -> set:
        """Extract skills from text using comprehensive skill keywords"""
        text_lower = text.lower()
        found_skills = set()
        
        # Comprehensive skill database
        skill_keywords = {
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'ruby', 'php', 
            'swift', 'kotlin', 'scala', 'rust', 'perl', 'r', 'matlab', 'golang',
            
            # Backend Frameworks
            'django', 'flask', 'fastapi', 'spring', 'spring boot', 'express', 'rails', 
            'laravel', 'asp.net', '.net', 'node.js', 'nodejs',
            
            # Frontend Frameworks
            'react', 'angular', 'vue', 'next.js', 'nextjs', 'vue.js',
            
            # Databases
            'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'dynamodb', 'cassandra',
            'redis', 'elasticsearch', 'oracle', 'sqlite', 'firebase', 'couchdb', 'nosql',
            
            # Cloud & DevOps
            'aws', 'amazon web services', 'azure', 'gcp', 'google cloud', 'docker', 
            'kubernetes', 'k8s', 'jenkins', 'git', 'github', 'gitlab', 'bitbucket',
            'ci/cd', 'cicd', 'terraform', 'ansible', 'puppet', 'chef', 'ec2', 's3',
            
            # Architecture & Design
            'microservices', 'micro-services', 'distributed systems', 'system design',
            'rest api', 'graphql', 'grpc', 'message queue', 'kafka', 'rabbitmq',
            'high availability', 'scalability', 'load balancing',
            
            # Testing
            'unit testing', 'integration testing', 'pytest', 'junit', 'selenium', 'cypress',
            'jest', 'mocha', 'chai', 'test driven development', 'tdd',
            
            # Methodologies
            'agile', 'scrum', 'kanban', 'bdd', 'continuous integration', 'continuous deployment',
        }
        
        # Direct matches
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.add(skill)
        
        # Extract from "Skills:" or "Technical Skills:" sections
        skills_section_patterns = [
            r'(?:skills|technical skills|technologies|tech stack|core competencies)[:\s]+([^\n]+(?:\n[•\-*][^\n]+)*)',
            r'##\s*(?:skills|technical skills)[^\n]*\n(.*?)(?=\n##|\Z)',
            r'###\s*(?:skills|technical skills)[^\n]*\n(.*?)(?=\n###|\Z)',
        ]
        
        for pattern in skills_section_patterns:
            matches = re.findall(pattern, text_lower, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Split by common delimiters
                words = re.split(r'[,•·•|•\n•-•*]', match)
                for word in words:
                    word = word.strip()
                    if len(word) > 2 and len(word) < 40 and not any(stop in word for stop in ['and', 'the', 'with']):
                        found_skills.add(word)
        
        # Extract from bullet points that look like skills
        bullet_lines = re.findall(r'[•\-*]\s*([a-z][a-z\s]+(?:[•\-*][a-z\s]+)*)', text_lower)
        for line in bullet_lines:
            line = line.strip()
            if len(line) < 60 and not any(word in line for word in ['experience', 'project', 'work', 'education', 'company']):
                # Split by commas or spaces
                parts = re.split(r'[,•·•|•\s]+', line)
                for part in parts:
                    part = part.strip()
                    if len(part) > 2 and len(part) < 30:
                        found_skills.add(part)
        
        return found_skills
    
    def _calculate_skills_match(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Calculate skills match with proper extraction"""
        
        # Extract skills from resume data
        resume_skills = set()
        
        # Method 1: From structured data
        skills_data = resume_data.get('skills', {})
        if isinstance(skills_data, dict):
            for category in ['technical', 'tools', 'languages', 'frameworks', 'skills', 'technologies']:
                items = skills_data.get(category, [])
                for item in items:
                    if isinstance(item, dict):
                        skill_name = item.get('name', '').lower().strip()
                        if skill_name:
                            resume_skills.add(skill_name)
                    else:
                        resume_skills.add(str(item).lower().strip())
        
        # Method 2: From raw text
        if resume_data.get('raw_text'):
            resume_skills.update(self._extract_skills_from_text(resume_data['raw_text']))
        
        # Extract skills from JD
        jd_skills = set()
        
        # Method 1: From structured JD data
        requirements = jd_data.get('requirements', {})
        if isinstance(requirements, dict):
            must_have = requirements.get('must_have', {})
            if isinstance(must_have, dict):
                for skill in must_have.get('skills', []):
                    if isinstance(skill, dict):
                        jd_skills.add(skill.get('name', '').lower().strip())
                    else:
                        jd_skills.add(str(skill).lower().strip())
            
            nice_to_have = requirements.get('nice_to_have', {})
            if isinstance(nice_to_have, dict):
                for skill in nice_to_have.get('skills', []):
                    if isinstance(skill, dict):
                        jd_skills.add(skill.get('name', '').lower().strip())
                    else:
                        jd_skills.add(str(skill).lower().strip())
        
        # Method 2: From JD raw text
        if jd_data.get('raw_text'):
            jd_skills.update(self._extract_skills_from_text(jd_data['raw_text']))
        
        # Method 3: Check skills_required field
        if jd_data.get('skills_required'):
            skills_list = jd_data.get('skills_required', '').split(',')
            for skill in skills_list:
                jd_skills.add(skill.lower().strip())
        
        # Method 4: From structured_json
        if jd_data.get('structured_json'):
            structured = jd_data.get('structured_json', {})
            if 'skills_required' in structured:
                skills = structured['skills_required']
                if isinstance(skills, list):
                    for skill in skills:
                        jd_skills.add(str(skill).lower().strip())
                elif isinstance(skills, str):
                    for skill in skills.split(','):
                        jd_skills.add(skill.lower().strip())
        
        # Skill mappings for better matching
        skill_mappings = {
            'python': ['python', 'python3', 'python 3', 'py'],
            'java': ['java', 'java8', 'java11', 'java17', 'j2ee'],
            'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda', 'amazon'],
            'microservices': ['microservices', 'micro-services', 'micro service', 'microservice'],
            'distributed systems': ['distributed systems', 'distributed computing', 'distributed'],
            'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'pl/sql', 't-sql'],
            'nosql': ['nosql', 'mongodb', 'dynamodb', 'cassandra', 'redis', 'couchdb'],
            'ci/cd': ['ci/cd', 'cicd', 'ci cd', 'continuous integration', 'continuous deployment', 'jenkins'],
            'docker': ['docker', 'container', 'containerization', 'dockerfile'],
            'kubernetes': ['kubernetes', 'k8s', 'kube'],
            'git': ['git', 'github', 'gitlab', 'bitbucket', 'version control'],
            'rest api': ['rest api', 'restful', 'restful api', 'rest'],
            'react': ['react', 'react.js', 'reactjs'],
            'javascript': ['javascript', 'js', 'ecmascript'],
        }
        
        # Expand JD skills using mappings
        expanded_jd_skills = set()
        for skill in jd_skills:
            expanded_jd_skills.add(skill)
            for main_skill, variations in skill_mappings.items():
                if skill == main_skill or skill in variations:
                    expanded_jd_skills.add(main_skill)
                    for var in variations:
                        expanded_jd_skills.add(var)
                elif any(var in skill for var in variations):
                    expanded_jd_skills.add(main_skill)
                    for var in variations:
                        expanded_jd_skills.add(var)
        
        # Find matches with improved logic
        matching = []
        missing = []
        
        for skill in expanded_jd_skills:
            matched = False
            for resume_skill in resume_skills:
                # Exact match
                if skill == resume_skill:
                    matched = True
                    break
                # Skill in resume skill
                if skill in resume_skill:
                    matched = True
                    break
                # Resume skill in skill
                if resume_skill in skill:
                    matched = True
                    break
                # Check against mappings
                for main_skill, variations in skill_mappings.items():
                    if skill == main_skill and resume_skill in variations:
                        matched = True
                        break
                    if resume_skill == main_skill and skill in variations:
                        matched = True
                        break
                    if skill in variations and resume_skill in variations:
                        matched = True
                        break
            
            if matched:
                if skill not in matching:
                    matching.append(skill)
            else:
                if skill not in missing and len(skill) > 2:
                    missing.append(skill)
        
        # Calculate score
        if len(expanded_jd_skills) > 0:
            score = len(matching) / len(expanded_jd_skills)
        else:
            score = 0.5
        
        logger.info(f"JD Skills: {len(jd_skills)} original, {len(expanded_jd_skills)} expanded")
        logger.info(f"Resume Skills: {len(resume_skills)}")
        logger.info(f"Matching Skills: {len(matching)} - {matching[:10]}")
        logger.info(f"Missing Skills: {len(missing)} - {missing[:10]}")
        
        return {
            'score': score,
            'matching': matching[:15],
            'missing': missing[:15],
            'required_missing': missing[:5],
            'preferred_missing': []
        }
    
    def _calculate_experience_match(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Calculate experience match with accurate calculation"""
        resume_experience = resume_data.get('experience', [])
        
        # Calculate total experience years
        total_years = 0
        matching_experience = []
        
        for exp in resume_experience:
            # Get duration years
            years = exp.get('duration_years', 0)
            if years > 0:
                total_years += years
            else:
                # Try to extract from dates
                start_date = str(exp.get('start_date', ''))
                end_date = str(exp.get('end_date', 'present'))
                
                # Extract year from start date
                start_year_match = re.search(r'\d{4}', start_date)
                if start_year_match:
                    start_year = int(start_year_match.group())
                    end_year = 2026  # Current year
                    if end_date and end_date.lower() != 'present':
                        end_year_match = re.search(r'\d{4}', end_date)
                        if end_year_match:
                            end_year = int(end_year_match.group())
                    years = end_year - start_year
                    total_years += years
            
            # Add job title
            title = exp.get('title', '')
            if title:
                matching_experience.append(title)
        
        # Get required experience from JD
        required_years = 0
        
        # From qualifications
        qualifications = jd_data.get('qualifications', {})
        if isinstance(qualifications, dict):
            required_years = qualifications.get('min_experience_years', 0)
            if required_years == 0:
                exp_req = qualifications.get('experience', [])
                if exp_req and isinstance(exp_req, list):
                    for exp in exp_req:
                        numbers = re.findall(r'\d+', str(exp))
                        if numbers:
                            required_years = int(numbers[0])
                            break
        
        # From raw JD text
        if required_years == 0 and jd_data.get('raw_text'):
            jd_text = jd_data['raw_text'].lower()
            patterns = [
                r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience)?',
                r'minimum\s+of\s+(\d+)\s*years?',
                r'(\d+)\s*\+\s*years?'
            ]
            for pattern in patterns:
                match = re.search(pattern, jd_text)
                if match:
                    required_years = int(match.group(1))
                    break
        
        # Calculate score
        if required_years > 0:
            if total_years >= required_years:
                # Exceeds or meets requirements
                if total_years >= required_years + 3:
                    score = 1.0
                elif total_years >= required_years + 1:
                    score = 0.98
                else:
                    score = 0.95
            else:
                # Below requirement
                score = max(0.5, (total_years / required_years) * 0.85)
        else:
            # No requirement, give high score if experience exists
            score = 0.9 if total_years > 0 else 0.6
        
        logger.info(f"Total Experience: {total_years:.1f} years")
        logger.info(f"Required Experience: {required_years} years")
        
        return {
            'score': score,
            'total_years': total_years,
            'required_years': required_years,
            'matching': matching_experience[:5],
            'missing': []
        }
    
    def _calculate_education_match(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Calculate education match"""
        resume_education = resume_data.get('education', [])
        
        # Education level mapping
        edu_levels = {
            'phd': 5, 'doctorate': 5, 'doctoral': 5,
            'master': 4, 'mba': 4, 'ms': 4, 'm.sc': 4, 'm.tech': 4, 'm.s.': 4,
            'bachelor': 3, 'bs': 3, 'ba': 3, 'b.sc': 3, 'b.tech': 3, 'be': 3, 'b.s.': 3,
            'associate': 2, 'diploma': 2,
            'high school': 1
        }
        
        # Get highest education level from resume
        highest_level = 0
        highest_degree = ''
        for edu in resume_education:
            degree = edu.get('degree', '').lower()
            for level_name, level_value in edu_levels.items():
                if level_name in degree:
                    if level_value > highest_level:
                        highest_level = level_value
                        highest_degree = degree
                    break
        
        # Get required education from JD
        qualifications = jd_data.get('qualifications', {})
        required_edu = 'bachelor'  # Default
        required_level = 3
        
        if isinstance(qualifications, dict):
            required_edu = qualifications.get('min_education', '').lower()
            if not required_edu:
                edu_list = qualifications.get('education', [])
                if edu_list:
                    required_edu = str(edu_list[0]).lower()
            
            # Determine required level
            for level_name, level_value in edu_levels.items():
                if level_name in required_edu:
                    required_level = level_value
                    break
        
        # Calculate score
        if highest_level >= required_level:
            score = 1.0
        elif highest_level > 0:
            score = max(0.5, highest_level / required_level)
        else:
            score = 0.4
        
        return {
            'score': score,
            'highest_degree': highest_degree,
            'required_degree': required_edu,
            'matching': [highest_degree] if highest_degree else [],
            'missing': [required_edu] if highest_level < required_level else []
        }
    
    def _calculate_keywords_match(self, resume_text: str, jd_data: Dict, jd_text: str = "") -> Dict:
        """Calculate keyword match"""
        
        # Get JD text
        if jd_text:
            jd_lower = jd_text.lower()
        else:
            jd_lower = jd_data.get('raw_text', '').lower()
        
        # Important keywords for tech roles
        important_keywords = [
            'distributed', 'scalable', 'microservices', 'architecture', 'backend',
            'api', 'rest', 'system design', 'high availability', 'performance',
            'optimization', 'caching', 'agile', 'scrum', 'code review', 'mentor',
            'cloud', 'aws', 'database', 'security', 'reliability'
        ]
        
        # Extract keywords from JD
        words = re.findall(r'\b[a-z][a-z]{3,}\b', jd_lower)
        word_freq = Counter(words)
        
        # Stop words
        stop_words = {'the', 'and', 'for', 'are', 'with', 'will', 'can', 'all', 'our', 'your',
                      'that', 'this', 'these', 'those', 'from', 'have', 'has', 'had', 'been',
                      'was', 'were', 'they', 'their', 'them', 'would', 'could', 'should'}
        
        # Get relevant keywords
        technical_keywords = []
        for word, freq in word_freq.most_common(40):
            if word not in stop_words and len(word) > 3 and freq >= 1:
                technical_keywords.append(word)
        
        # Add important keywords that appear in JD
        for keyword in important_keywords:
            if keyword in jd_lower and keyword not in technical_keywords:
                technical_keywords.append(keyword)
        
        if not technical_keywords:
            return {'score': 0.8, 'matching': [], 'missing': []}
        
        # Check which keywords appear in resume
        resume_lower = resume_text.lower()
        matching = []
        missing = []
        
        for keyword in technical_keywords[:30]:
            if keyword in resume_lower:
                matching.append(keyword)
            else:
                missing.append(keyword)
        
        # Calculate score
        score = len(matching) / len(technical_keywords) if technical_keywords else 0.7
        
        return {
            'score': score,
            'matching': matching[:15],
            'missing': missing[:15]
        }
    
    def _calculate_formatting_score(self, resume_text: str) -> Dict:
        """Calculate formatting score"""
        issues = []
        score = 0.75
        
        # Check for section headers
        sections = ['experience', 'education', 'skills', 'projects', 'work', 'summary']
        found_sections = sum(1 for section in sections if re.search(r'\b' + section + r'\b', resume_text.lower()))
        
        if found_sections < 3:
            score -= 0.15
            issues.append("Add clear section headers")
        
        # Check for bullet points
        bullet_points = len(re.findall(r'^[•\-*]\s', resume_text, re.MULTILINE))
        if bullet_points < 3:
            score -= 0.1
            issues.append("Use bullet points for achievements")
        elif bullet_points > 8:
            score += 0.05
        
        # Check length
        word_count = len(resume_text.split())
        if 400 <= word_count <= 800:
            score += 0.05
        elif word_count < 300:
            score -= 0.1
            issues.append("Resume is too short")
        elif word_count > 1000:
            score -= 0.05
            issues.append("Resume is too long")
        
        return {'score': max(0.5, min(score, 0.95)), 'issues': issues}
    
    def _calculate_completeness_score(self, resume_data: Dict) -> Dict:
        """Calculate completeness score"""
        required_sections = ['personal_info', 'skills', 'experience', 'education']
        present = sum(1 for section in required_sections if resume_data.get(section))
        
        score = present / len(required_sections)
        
        # Bonus for additional sections
        if resume_data.get('projects'):
            score += 0.1
        if resume_data.get('certifications'):
            score += 0.05
        
        missing_info = []
        if not resume_data.get('personal_info', {}).get('email'):
            missing_info.append("Email")
        if not resume_data.get('personal_info', {}).get('phone'):
            missing_info.append("Phone")
        
        return {'score': min(score, 0.95), 'missing_info': missing_info}
    
    def _generate_section_suggestions(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Generate section suggestions"""
        suggestions = {'skills': [], 'experience': [], 'summary': [], 'education': [], 'projects': []}
        
        # Skills suggestions
        if jd_data.get('requirements', {}).get('must_have', {}).get('skills'):
            missing = self._calculate_skills_match(resume_data, jd_data).get('missing', [])[:3]
            if missing:
                suggestions['skills'].append(f"Add missing skills: {', '.join(missing)}")
        
        return suggestions
    
    def _check_spelling_errors(self, text: str) -> List[Dict]:
        """Check spelling errors"""
        common_mistakes = {
            'recieve': 'receive', 'acheive': 'achieve', 'comittment': 'commitment',
            'maintainance': 'maintenance', 'managment': 'management', 'developement': 'development'
        }
        
        errors = []
        for word, correction in common_mistakes.items():
            if word in text.lower():
                errors.append({'word': word, 'suggestion': correction, 'context': ''})
        
        return errors
    
    def _check_grammar_issues(self, text: str) -> List[Dict]:
        """Check grammar issues"""
        issues = []
        
        if re.search(r'\bwas\s+\w+ed\b', text.lower()):
            issues.append({'type': 'Passive Voice', 'suggestion': 'Use active voice', 'example': None})
        
        return issues
    
    def _analyze_style_improvements(self, resume_text: str, jd_data: Dict) -> List[str]:
        """Analyze style improvements"""
        improvements = []
        
        action_verbs = ['achieved', 'developed', 'implemented', 'designed', 'built', 'created', 'led']
        found = sum(1 for verb in action_verbs if verb in resume_text.lower())
        
        if found < 3:
            improvements.append("Use more action verbs to describe achievements")
        
        return improvements
    
    def _analyze_formatting_issues(self, resume_text: str) -> List[str]:
        """Analyze formatting issues"""
        issues = []
        
        if not re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', resume_text):
            issues.append("Missing email address")
        
        if not re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', resume_text):
            issues.append("Missing phone number")
        
        return issues
    
    def _identify_strengths_weaknesses(self, skills: Dict, experience: Dict, 
                                       education: Dict, keywords: Dict) -> Tuple[List, List]:
        """Identify strengths and weaknesses"""
        strengths = []
        weaknesses = []
        
        if skills['score'] >= 0.8:
            strengths.append(f"Strong skills match with {len(skills['matching'])} relevant skills")
        elif skills['score'] < 0.5:
            weaknesses.append(f"Missing {len(skills['missing'])} key skills")
        
        if experience['score'] >= 0.8:
            strengths.append(f"Experience level meets requirements ({experience['total_years']:.0f} years)")
        elif experience['score'] < 0.5:
            weaknesses.append("Experience below requirements")
        
        if education['score'] >= 0.9:
            strengths.append("Educational qualifications meet requirements")
        
        return strengths, weaknesses
    
    def _generate_improvement_suggestions(self, skills: Dict, experience: Dict,
                                         education: Dict, keywords: Dict,
                                         formatting: Dict, completeness: Dict,
                                         spelling_errors: List, grammar_issues: List) -> Dict:
        """Generate improvement suggestions"""
        suggestions = {'skills': [], 'experience': [], 'formatting': [], 'content': []}
        
        if skills['missing']:
            suggestions['skills'].append(f"Add missing skills: {', '.join(skills['missing'][:3])}")
        
        if experience['score'] < 0.7:
            suggestions['experience'].append("Highlight achievements with metrics and numbers")
        
        return suggestions
    
    def _generate_comprehensive_recommendations(self, improvements: Dict, 
                                               strengths: List, weaknesses: List) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        if weaknesses:
            recommendations.append(f"Priority: {weaknesses[0]}")
        
        if improvements.get('skills'):
            recommendations.append(improvements['skills'][0])
        
        recommendations.append("Tailor your resume to match job requirements")
        recommendations.append("Use keywords from the job description")
        
        return recommendations[:5]
    
    def _generate_detailed_feedback(self, overall_score: float, skills: Dict,
                                   experience: Dict, education: Dict, keywords: Dict,
                                   strengths: List, weaknesses: List, 
                                   recommendations: List) -> str:
        """Generate detailed feedback"""
        parts = []
        
        if overall_score >= 85:
            parts.append("Excellent match! Your resume is highly aligned with this position.")
        elif overall_score >= 70:
            parts.append("Good match with strong alignment to requirements.")
        elif overall_score >= 55:
            parts.append("Moderate match. Some improvements recommended.")
        else:
            parts.append("Low match. Consider significant improvements.")
        
        parts.append(f"\nOverall Score: {overall_score:.0f}%")
        parts.append(f"Skills: {skills['score']*100:.0f}%")
        parts.append(f"Experience: {experience['score']*100:.0f}%")
        
        if skills['missing']:
            parts.append(f"\nMissing Skills: {', '.join(skills['missing'][:3])}")
        
        return '\n'.join(parts)
    
    def _get_context(self, text: str, word: str, window: int = 10) -> str:
        """Get context around a word"""
        words = text.split()
        for i, w in enumerate(words):
            if word in w.lower():
                start = max(0, i - window)
                end = min(len(words), i + window + 1)
                return ' '.join(words[start:end])
        return ""