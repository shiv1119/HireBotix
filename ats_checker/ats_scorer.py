# ats_scorer.py - Market-Leading ATS Scorer with Intelligent Suggestions

import re
from typing import Dict, List, Any, Tuple
from collections import Counter
import logging
from datetime import datetime
import math

logger = logging.getLogger(__name__)

class AdvancedATSScorer:
    """
    Market-leading ATS Scorer with intelligent suggestions,
    number extraction, and resume restructuring recommendations.
    """

    def __init__(self):
        self.weights = {
            'skills': 0.35,
            'experience': 0.25,
            'education': 0.10,
            'keywords': 0.15,
            'impact_metrics': 0.10,  # New: measures quantifiable achievements
            'formatting': 0.03,
            'completeness': 0.02
        }
        
        # Industry-specific keyword databases
        self.tech_keywords = {
            'languages': ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#', 'swift', 'kotlin', 'ruby', 'scala', 'php'],
            'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'rails', 'fastapi', 'tensorflow', 'pytorch'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'gitlab', 'github actions'],
            'databases': ['postgresql', 'mongodb', 'mysql', 'redis', 'elasticsearch', 'cassandra', 'dynamodb'],
            'architecture': ['microservices', 'event-driven', 'serverless', 'rest api', 'graphql', 'grpc', 'kafka', 'rabbitmq']
        }
        
        # Action verbs for different contexts
        self.action_verbs = {
            'achievement': ['achieved', 'delivered', 'launched', 'completed', 'executed', 'generated'],
            'improvement': ['improved', 'increased', 'enhanced', 'optimized', 'accelerated', 'boosted'],
            'leadership': ['led', 'managed', 'directed', 'coordinated', 'mentored', 'supervised'],
            'innovation': ['developed', 'created', 'built', 'designed', 'architected', 'implemented'],
            'efficiency': ['reduced', 'cut', 'saved', 'streamlined', 'automated', 'consolidated']
        }
        
        # Metric patterns to extract
        self.metric_patterns = {
            'percentage': r'(\d+(?:\.\d+)?)\s*%',
            'time': r'(\d+)\s*(?:month|year|day|week|hour)s?',
            'money': r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:million|billion|k|M|B)?',
            'count': r'(\d+(?:,\d+)*)\s*(?:users|customers|clients|projects|products|features|teams)',
            'performance': r'(\d+(?:\.\d+)?)\s*(?:x|times|fold)\s*(?:faster|better|improvement)'
        }
    
    def calculate_comprehensive_score(self, resume_data: Dict, jd_data: Dict, 
                                     resume_text: str, jd_text: str) -> Dict[str, Any]:
        """Main calculation method with all enhancements"""
        
        logger.info("=" * 70)
        logger.info("🚀 Starting Advanced ATS Score Calculation")
        logger.info("=" * 70)
        
        # Calculate all component scores
        skills_result = self._calculate_skills_match(resume_data, jd_data, resume_text, jd_text)
        experience_result = self._calculate_experience_match(resume_data, jd_data)
        education_result = self._calculate_education_match(resume_data, jd_data)
        keywords_result = self._calculate_keywords_match(resume_text, jd_text)
        impact_result = self._calculate_impact_metrics(resume_text)
        formatting_result = self._calculate_formatting_score(resume_text)
        completeness_result = self._calculate_completeness_score(resume_data)
        
        # Log all scores
        self._log_scores({
            'Skills': skills_result['score'],
            'Experience': experience_result['score'],
            'Education': education_result['score'],
            'Keywords': keywords_result['score'],
            'Impact Metrics': impact_result['score'],
            'Formatting': formatting_result['score'],
            'Completeness': completeness_result['score']
        })
        
        # Calculate weighted overall score
        overall_score = (
            self.weights['skills'] * skills_result['score'] +
            self.weights['experience'] * experience_result['score'] +
            self.weights['education'] * education_result['score'] +
            self.weights['keywords'] * keywords_result['score'] +
            self.weights['impact_metrics'] * impact_result['score'] +
            self.weights['formatting'] * formatting_result['score'] +
            self.weights['completeness'] * completeness_result['score']
        ) * 100
        
        # Generate intelligent suggestions
        restructuring_suggestions = self._generate_restructuring_suggestions(resume_text, jd_text)
        number_suggestions = self._generate_number_suggestions(resume_text, jd_text, skills_result)
        section_rewrites = self._generate_section_rewrites(resume_text, jd_text)
        
        # Quality analysis
        quality_analysis = self._analyze_quality(resume_text)
        
        # Generate strengths and weaknesses
        strengths, weaknesses = self._identify_strengths_weaknesses(
            skills_result, experience_result, impact_result, keywords_result
        )
        
        # Generate improvement plan
        improvement_plan = self._generate_improvement_plan(
            skills_result, impact_result, keywords_result, restructuring_suggestions,
            number_suggestions, section_rewrites, quality_analysis
        )
        
        return {
            'overall_score': round(overall_score, 2),
            'match_percentage': round(overall_score, 2),
            'skills_match_score': round(skills_result['score'] * 100, 2),
            'experience_match_score': round(experience_result['score'] * 100, 2),
            'education_match_score': round(education_result['score'] * 100, 2),
            'keyword_match_score': round(keywords_result['score'] * 100, 2),
            'impact_metrics_score': round(impact_result['score'] * 100, 2),
            'formatting_score': round(formatting_result['score'] * 100, 2),
            'completeness_score': round(completeness_result['score'] * 100, 2),
            
            # Detailed matching data
            'matching_skills': skills_result['matching'][:15],
            'missing_skills': skills_result['missing'][:15],
            'matching_keywords': keywords_result['matching'][:15],
            'missing_keywords': keywords_result['missing'][:15],
            'matching_experience': experience_result['matching'],
            'missing_experience': experience_result['missing'],
            
            # New: Intelligent suggestions
            'restructuring_suggestions': restructuring_suggestions,
            'number_suggestions': number_suggestions,
            'section_rewrites': section_rewrites,
            'quality_analysis': quality_analysis,
            
            # Standard feedback
            'strengths': strengths,
            'weaknesses': weaknesses,
            'improvement_plan': improvement_plan,
            'section_suggestions': self._generate_section_suggestions(resume_data, jd_data),
            'spelling_errors': self._check_spelling_errors(resume_text),
            'grammar_issues': self._check_grammar_issues(resume_text),
            'style_improvements': quality_analysis['style_recommendations'],
            'formatting_issues': formatting_result['issues'],
            'recommendations': improvement_plan['quick_wins'][:5],
            'detailed_feedback': self._generate_detailed_feedback(
                overall_score, skills_result, experience_result, 
                impact_result, strengths, weaknesses
            )
        }
    
    def _calculate_skills_match(self, resume_data: Dict, jd_data: Dict, 
                                resume_text: str, jd_text: str) -> Dict:
        """Enhanced skills matching with semantic similarity"""
        
        # Extract skills from multiple sources
        resume_skills = self._extract_comprehensive_skills(resume_data, resume_text)
        jd_skills = self._extract_comprehensive_skills(jd_data, jd_text)
        
        # Calculate semantic similarity for skill matching
        matching = []
        missing = []
        partial_matches = []
        
        for jd_skill in jd_skills:
            best_match = None
            best_score = 0
            
            for resume_skill in resume_skills:
                # Exact match
                if jd_skill.lower() == resume_skill.lower():
                    best_match = resume_skill
                    best_score = 1.0
                    break
                
                # Contains match
                if jd_skill.lower() in resume_skill.lower() or resume_skill.lower() in jd_skill.lower():
                    score = 0.9
                    if score > best_score:
                        best_match = resume_skill
                        best_score = score
                
                # Similarity score
                else:
                    score = self._calculate_similarity(jd_skill.lower(), resume_skill.lower())
                    if score > best_score and score > 0.6:
                        best_match = resume_skill
                        best_score = score
            
            if best_match and best_score >= 0.8:
                matching.append(jd_skill)
            elif best_match and best_score >= 0.6:
                partial_matches.append({'required': jd_skill, 'found': best_match})
            else:
                missing.append(jd_skill)
        
        # Calculate weighted score
        total_skills = len(jd_skills)
        if total_skills > 0:
            score = (len(matching) + (len(partial_matches) * 0.5)) / total_skills
        else:
            score = 0.7
        
        return {
            'score': min(score, 1.0),
            'matching': matching,
            'partial_matches': partial_matches,
            'missing': missing
        }
    
    def _extract_comprehensive_skills(self, data: Dict, text: str) -> List[str]:
        """Extract skills from multiple sources"""
        skills = set()
        
        # From structured data
        if isinstance(data, dict):
            skills_data = data.get('skills', {})
            if isinstance(skills_data, dict):
                for category in ['technical', 'tools', 'frameworks', 'languages', 'technologies']:
                    items = skills_data.get(category, [])
                    for item in items:
                        if isinstance(item, dict):
                            skill_name = item.get('name', '').strip()
                            if skill_name:
                                skills.add(skill_name.lower())
                        elif isinstance(item, str):
                            skills.add(item.lower())
            
            # From experience section
            experiences = data.get('experience', [])
            for exp in experiences:
                responsibilities = exp.get('responsibilities', [])
                for resp in responsibilities:
                    # Extract potential skills from responsibilities
                    for category in self.tech_keywords.values():
                        for skill in category:
                            if skill.lower() in resp.lower():
                                skills.add(skill.lower())
        
        # From raw text - skills section
        skills_pattern = r'(?:skills|technical skills|technologies|tech stack)[:\s]+\n?(.*?)(?:\n\n|\n[A-Z]|\Z)'
        match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            skills_text = match.group(1)
            # Extract comma or bullet separated skills
            skill_items = re.split(r'[,•·●•\n•-•*•|•\s]+', skills_text)
            for skill in skill_items:
                skill = skill.strip().lower()
                if len(skill) > 2 and len(skill) < 40:
                    skills.add(skill)
        
        # From all text - look for skill keywords
        text_lower = text.lower()
        for category in self.tech_keywords.values():
            for skill in category:
                if skill.lower() in text_lower:
                    skills.add(skill.lower())
        
        return list(skills)
    
    def _calculate_experience_match(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Enhanced experience matching with role relevance"""
        
        resume_experience = resume_data.get('experience', [])
        
        # Calculate total experience
        total_years = 0
        relevant_years = 0
        matching_titles = []
        
        # Get job title from JD
        job_title = ""
        if isinstance(jd_data, dict):
            metadata = jd_data.get('job_metadata', {})
            job_title = metadata.get('title', '').lower()
        
        for exp in resume_experience:
            # Calculate years
            years = self._calculate_duration_years(exp)
            total_years += years
            
            # Check relevance
            title = exp.get('title', '').lower()
            if job_title and (job_title in title or any(word in title for word in job_title.split())):
                relevant_years += years
                matching_titles.append(exp.get('title', ''))
        
        # Get required experience from JD
        required_years = 0
        if isinstance(jd_data, dict):
            qualifications = jd_data.get('qualifications', {})
            required_years = qualifications.get('min_experience_years', 0)
        
        # Calculate score
        if required_years > 0:
            # Use relevant years if available, otherwise total
            effective_years = relevant_years if relevant_years > 0 else total_years
            
            if effective_years >= required_years:
                # Exceeds requirements bonus
                bonus = min(0.1, (effective_years - required_years) / 20)
                score = min(1.0, 0.95 + bonus)
            else:
                score = max(0.3, effective_years / required_years * 0.8)
        else:
            score = 0.8 if total_years > 0 else 0.5
        
        return {
            'score': score,
            'total_years': round(total_years, 1),
            'relevant_years': round(relevant_years, 1),
            'required_years': required_years,
            'matching': matching_titles[:3],
            'missing': [] if total_years >= required_years else [f"{required_years - total_years:.0f} more years"]
        }
    
    def _calculate_duration_years(self, exp: Dict) -> float:
        """Calculate duration in years from experience entry"""
        years = exp.get('duration_years', 0)
        
        if years == 0:
            start_date = str(exp.get('start_date', ''))
            end_date = str(exp.get('end_date', 'present'))
            
            # Extract years
            start_match = re.search(r'\d{4}', start_date)
            end_match = re.search(r'\d{4}', end_date) if end_date.lower() != 'present' else None
            
            if start_match:
                start_year = int(start_match.group())
                end_year = datetime.now().year if not end_match else int(end_match.group())
                years = end_year - start_year
        
        return years
    
    def _calculate_education_match(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Enhanced education matching with field relevance"""
        
        # Education level mapping with scores
        edu_mapping = {
            'phd': {'level': 5, 'score': 1.0},
            'master': {'level': 4, 'score': 0.95},
            'mba': {'level': 4, 'score': 0.95},
            'bachelor': {'level': 3, 'score': 0.85},
            'associate': {'level': 2, 'score': 0.7},
            'diploma': {'level': 2, 'score': 0.65},
            'certification': {'level': 1, 'score': 0.5}
        }
        
        # Get highest education from resume
        resume_education = resume_data.get('education', [])
        highest_level = 0
        highest_score = 0
        field_of_study = ""
        
        for edu in resume_education:
            degree = edu.get('degree', '').lower()
            field = edu.get('field', '').lower()
            
            for level_name, level_info in edu_mapping.items():
                if level_name in degree:
                    if level_info['level'] > highest_level:
                        highest_level = level_info['level']
                        highest_score = level_info['score']
                        field_of_study = field
                    break
        
        # Get required education from JD
        required_degree = ""
        required_field = ""
        if isinstance(jd_data, dict):
            qualifications = jd_data.get('qualifications', {})
            required_degree = qualifications.get('min_education', '').lower()
            
            # Extract field from JD
            jd_text = jd_data.get('raw_text', '').lower()
            field_patterns = [r'degree in (\w+)', r'background in (\w+)', r'field of (\w+)']
            for pattern in field_patterns:
                match = re.search(pattern, jd_text)
                if match:
                    required_field = match.group(1)
                    break
        
        # Calculate match
        required_level = 0
        for level_name, level_info in edu_mapping.items():
            if level_name in required_degree:
                required_level = level_info['level']
                break
        
        if required_level > 0:
            if highest_level >= required_level:
                level_score = 1.0
            else:
                level_score = max(0.3, highest_level / required_level)
        else:
            level_score = 0.8
        
        # Field relevance bonus
        field_bonus = 0
        if required_field and field_of_study:
            if required_field in field_of_study or field_of_study in required_field:
                field_bonus = 0.1
        
        score = min(1.0, level_score + field_bonus)
        
        return {
            'score': score,
            'highest_degree': highest_score,
            'required_degree': required_degree,
            'matching': [field_of_study] if field_of_study else [],
            'missing': [required_degree] if highest_level < required_level else []
        }
    
    def _calculate_keywords_match(self, resume_text: str, jd_text: str) -> Dict:
        """Enhanced keyword matching with TF-IDF"""
        
        # Extract important keywords from JD
        jd_words = re.findall(r'\b[a-z]{4,}\b', jd_text.lower())
        
        # Remove stop words
        stop_words = {'that', 'this', 'these', 'those', 'with', 'from', 'have', 'will', 'can', 
                     'should', 'would', 'could', 'their', 'they', 'them', 'about', 'which',
                     'what', 'when', 'where', 'who', 'why', 'how', 'also', 'very', 'just'}
        
        # Count frequencies
        word_freq = Counter([w for w in jd_words if w not in stop_words])
        
        # Get top keywords (appear 2+ times or high importance)
        important_keywords = []
        technical_boost = set()
        for word in self.tech_keywords['languages'] + self.tech_keywords['frameworks'] + self.tech_keywords['cloud']:
            technical_boost.add(word)
        
        for word, count in word_freq.most_common(50):
            if count >= 2 or word in technical_boost:
                important_keywords.append(word)
        
        # Check matches
        resume_lower = resume_text.lower()
        matching = []
        missing = []
        
        for keyword in important_keywords[:25]:
            if keyword in resume_lower:
                matching.append(keyword)
            else:
                missing.append(keyword)
        
        # Calculate score with weighting for technical terms
        total_weight = 0
        matched_weight = 0
        
        for keyword in important_keywords[:25]:
            weight = 2 if keyword in technical_boost else 1
            total_weight += weight
            if keyword in resume_lower:
                matched_weight += weight
        
        score = matched_weight / total_weight if total_weight > 0 else 0.7
        
        return {
            'score': score,
            'matching': matching[:15],
            'missing': missing[:15]
        }
    
    def _calculate_impact_metrics(self, resume_text: str) -> Dict:
        """Calculate impact metrics score - measures quantifiable achievements"""
        
        metrics_found = {
            'percentage': [],
            'money': [],
            'time': [],
            'count': [],
            'performance': []
        }
        
        # Extract metrics
        for metric_type, pattern in self.metric_patterns.items():
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            metrics_found[metric_type] = matches
        
        # Calculate score based on metrics present
        total_metrics = sum(len(v) for v in metrics_found.values())
        
        # Bonus for variety of metrics
        variety_bonus = len([k for k, v in metrics_found.items() if len(v) > 0]) / 5
        
        if total_metrics >= 10:
            score = 1.0
        elif total_metrics >= 7:
            score = 0.9
        elif total_metrics >= 5:
            score = 0.8
        elif total_metrics >= 3:
            score = 0.6
        elif total_metrics >= 1:
            score = 0.4
        else:
            score = 0.1
        
        # Add variety bonus
        score = min(1.0, score + (variety_bonus * 0.1))
        
        # Generate metric suggestions
        suggestions = []
        if total_metrics < 3:
            suggestions.append("Add quantifiable achievements with percentages, numbers, or dollar amounts")
        if len(metrics_found['percentage']) == 0:
            suggestions.append("Include percentage improvements (e.g., 'increased efficiency by 25%')")
        if len(metrics_found['money']) == 0:
            suggestions.append("Add cost savings or revenue figures (e.g., 'saved $500K annually')")
        if len(metrics_found['time']) == 0:
            suggestions.append("Include time-based achievements (e.g., 'delivered project 2 months early')")
        
        return {
            'score': score,
            'metrics_found': {k: len(v) for k, v in metrics_found.items()},
            'total_metrics': total_metrics,
            'suggestions': suggestions
        }
    
    def _generate_restructuring_suggestions(self, resume_text: str, jd_text: str) -> Dict:
        """Generate suggestions for restructuring resume sections"""
        
        suggestions = {
            'order_changes': [],
            'new_sections': [],
            'section_renames': [],
            'priority_shifts': []
        }
        
        # Check current sections
        sections_present = {
            'summary': bool(re.search(r'(?:summary|profile|about me)', resume_text, re.IGNORECASE)),
            'experience': bool(re.search(r'(?:experience|work history|employment)', resume_text, re.IGNORECASE)),
            'skills': bool(re.search(r'(?:skills|technical skills|technologies)', resume_text, re.IGNORECASE)),
            'education': bool(re.search(r'(?:education|academic background)', resume_text, re.IGNORECASE)),
            'projects': bool(re.search(r'(?:projects|side projects|personal projects)', resume_text, re.IGNORECASE)),
            'certifications': bool(re.search(r'(?:certifications|certificates|credentials)', resume_text, re.IGNORECASE))
        }
        
        # Suggest missing sections
        if not sections_present['summary']:
            suggestions['new_sections'].append({
                'section': 'Professional Summary',
                'template': 'Results-driven [Job Title] with X+ years of experience in [Industry]. Proven track record of [Key Achievement 1] and [Key Achievement 2]. Expert in [Key Skill 1], [Key Skill 2], and [Key Skill 3].'
            })
        
        if not sections_present['projects'] and 'project' in jd_text.lower():
            suggestions['new_sections'].append({
                'section': 'Key Projects',
                'template': 'Project Name: [Project Description]\n• Achieved [specific outcome] using [technologies]\n• Resulted in [quantifiable result]'
            })
        
        if not sections_present['skills']:
            suggestions['new_sections'].append({
                'section': 'Technical Skills',
                'template': '• Programming: [list languages]\n• Frameworks: [list frameworks]\n• Tools: [list tools]\n• Databases: [list databases]'
            })
        
        # Suggest section renames for better ATS parsing
        if re.search(r'work', resume_text, re.IGNORECASE) and not re.search(r'experience', resume_text, re.IGNORECASE):
            suggestions['section_renames'].append({
                'current': 'Work',
                'suggested': 'Professional Experience',
                'reason': 'ATS systems better recognize "Professional Experience"'
            })
        
        if re.search(r'tech skills', resume_text, re.IGNORECASE) and not re.search(r'skills', resume_text, re.IGNORECASE):
            suggestions['section_renames'].append({
                'current': 'Tech Skills',
                'suggested': 'Technical Skills',
                'reason': 'More standard section header for ATS'
            })
        
        # Suggest priority shifts based on JD
        if 'certification' in jd_text.lower() and not sections_present['certifications']:
            suggestions['priority_shifts'].append({
                'action': 'Add Certifications section',
                'priority': 'High',
                'reason': 'Job description emphasizes certifications'
            })
        
        if 'project' in jd_text.lower() and 'project' in jd_text.lower().count('project') > 2:
            suggestions['priority_shifts'].append({
                'action': 'Expand Projects section',
                'priority': 'High',
                'reason': 'Multiple project mentions in job description'
            })
        
        return suggestions
    
    def _generate_number_suggestions(self, resume_text: str, jd_text: str, skills_result: Dict) -> List[Dict]:
        """Generate specific number/metric suggestions for each experience bullet"""
        
        suggestions = []
        
        # Extract existing experience bullets
        experience_section = re.search(r'(?:experience|work history)[:\s]+\n?(.*?)(?:\n\n(?:education|skills|projects)|\Z)', 
                                       resume_text, re.IGNORECASE | re.DOTALL)
        
        if experience_section:
            bullets = re.findall(r'[•·●\-]\s*([^\n]+)', experience_section.group(1))
            
            for i, bullet in enumerate(bullets[:5]):  # Top 5 bullets
                suggestion = self._enhance_bullet_with_numbers(bullet, jd_text, skills_result['matching'][:3])
                if suggestion:
                    suggestions.append(suggestion)
        
        # General number suggestions for common scenarios
        common_scenarios = [
            {
                'scenario': 'team leadership',
                'template': 'Led team of [number] to achieve [result], improving [metric] by [percentage]%',
                'examples': ['Led team of 5 engineers', 'Managed team of 8 developers']
            },
            {
                'scenario': 'performance improvement',
                'template': 'Improved [system/process] performance by [percentage]%, resulting in [time/money] savings',
                'examples': ['Improved API response time by 40%', 'Optimized database queries reducing load time by 60%']
            },
            {
                'scenario': 'project delivery',
                'template': 'Delivered [project name] [timeframe] ahead of schedule, resulting in [outcome]',
                'examples': ['Delivered 3 months early', 'Completed project 2 weeks ahead of deadline']
            },
            {
                'scenario': 'cost reduction',
                'template': 'Reduced [cost type] by [amount] ([percentage]%) through [action taken]',
                'examples': ['Reduced AWS costs by $50K (30%)', 'Cut operational expenses by 25%']
            },
            {
                'scenario': 'revenue generation',
                'template': 'Generated [amount] in [revenue/savings] by implementing [solution]',
                'examples': ['Generated $1M in new revenue', 'Created $500K annual recurring revenue']
            },
            {
                'scenario': 'user/customer impact',
                'template': 'Served [number] [users/customers], achieving [metric] satisfaction rate',
                'examples': ['Served 1M+ daily active users', 'Supported 500 enterprise clients']
            }
        ]
        
        # Add scenario-based suggestions
        text_lower = resume_text.lower()
        for scenario in common_scenarios:
            if scenario['scenario'] in text_lower:
                # Check if already has numbers
                has_numbers = bool(re.search(r'\d+', text_lower))
                if not has_numbers:
                    suggestions.append({
                        'original_context': scenario['scenario'],
                        'suggestion': scenario['template'],
                        'examples': scenario['examples'],
                        'impact': 'High'
                    })
        
        return suggestions
    
    def _enhance_bullet_with_numbers(self, bullet: str, jd_text: str, key_skills: List) -> Dict:
        """Enhance a specific bullet point with number suggestions"""
        
        # Check if already has numbers
        if re.search(r'\d+', bullet):
            return None
        
        # Determine bullet type
        bullet_lower = bullet.lower()
        
        suggestion = {
            'original': bullet,
            'suggestions': [],
            'example': None
        }
        
        # Type 1: Improvement statements
        improvement_keywords = ['improve', 'enhance', 'optimize', 'increase', 'boost']
        if any(keyword in bullet_lower for keyword in improvement_keywords):
            suggestion['suggestions'].append("Add percentage improvement (e.g., 'improved by 25%')")
            suggestion['suggestions'].append("Add time frame (e.g., 'within 3 months')")
            suggestion['example'] = bullet + f" by 30%, resulting in $100K annual savings"
        
        # Type 2: Development statements
        dev_keywords = ['develop', 'build', 'create', 'implement', 'launch']
        if any(keyword in bullet_lower for keyword in dev_keywords):
            suggestion['suggestions'].append("Add user/customer impact (e.g., 'serving 10,000 users')")
            suggestion['suggestions'].append("Add time to completion (e.g., 'delivered 2 months early')")
            suggestion['example'] = bullet + f", serving 50,000+ daily active users"
        
        # Type 3: Leadership statements
        leadership_keywords = ['lead', 'manage', 'direct', 'supervise', 'mentor']
        if any(keyword in bullet_lower for keyword in leadership_keywords):
            suggestion['suggestions'].append("Add team size (e.g., 'led team of 8')")
            suggestion['suggestions'].append("Add project impact (e.g., 'completed $2M project')")
            suggestion['example'] = bullet + f" of 6 engineers, delivering $1.5M in annual value"
        
        # Type 4: Process statements
        process_keywords = ['automate', 'streamline', 'reduce', 'eliminate', 'cut']
        if any(keyword in bullet_lower for keyword in process_keywords):
            suggestion['suggestions'].append("Add time saved (e.g., 'saving 20 hours/week')")
            suggestion['suggestions'].append("Add cost reduction (e.g., 'reducing costs by 40%')")
            suggestion['example'] = bullet + f", reducing processing time by 65%"
        
        # Add skill-specific suggestions
        if key_skills and any(skill in bullet_lower for skill in key_skills):
            suggestion['suggestions'].append(f"Highlight {key_skills[0]} expertise with metric")
        
        return suggestion if suggestion['suggestions'] else None
    
    def _generate_section_rewrites(self, resume_text: str, jd_text: str) -> Dict:
        """Generate specific rewrite examples for sections"""
        
        rewrites = {
            'summary': None,
            'experience': [],
            'skills': None
        }
        
        # Extract current summary
        summary_match = re.search(r'(?:summary|profile)[:\s]+\n?(.*?)(?:\n\n|\Z)', 
                                  resume_text, re.IGNORECASE | re.DOTALL)
        
        if summary_match:
            current_summary = summary_match.group(1).strip()
            
            # Extract key terms from JD for better summary
            jd_terms = re.findall(r'\b[A-Z][a-z]{3,}\b', jd_text)
            key_terms = list(set([term.lower() for term in jd_terms if len(term) > 4]))[:5]
            
            if key_terms:
                rewrites['summary'] = {
                    'current': current_summary[:200],
                    'suggested': f"Results-driven professional with expertise in {', '.join(key_terms[:3])}. {current_summary[:150]}",
                    'key_additions': key_terms[:3]
                }
        
        # Extract experience bullets to rewrite
        experience_section = re.search(r'(?:experience|work history)[:\s]+\n?(.*?)(?:\n\n(?:education|skills)|\Z)',
                                       resume_text, re.IGNORECASE | re.DOTALL)
        
        if experience_section:
            bullets = re.findall(r'[•·●\-]\s*([^\n]+)', experience_section.group(1))
            
            for bullet in bullets[:2]:  # Top 2 bullets
                if len(bullet) > 30 and not re.search(r'\d+', bullet):
                    # Generate STAR format rewrite
                    rewrites['experience'].append({
                        'original': bullet[:100],
                        'star_format': f"Situation: {bullet}\nTask: [specific responsibility]\nAction: [action taken]\nResult: [quantifiable outcome]",
                        'improved_version': bullet + f", achieving [specific metric]"
                    })
        
        return rewrites
    
    def _analyze_quality(self, resume_text: str) -> Dict:
        """Comprehensive quality analysis"""
        
        analysis = {
            'action_verbs': [],
            'style_recommendations': [],
            'strength_areas': [],
            'weakness_areas': []
        }
        
        # Check action verbs
        found_verbs = []
        for category, verbs in self.action_verbs.items():
            for verb in verbs:
                if verb in resume_text.lower():
                    found_verbs.append(verb)
        
        analysis['action_verbs'] = list(set(found_verbs))[:10]
        
        if len(found_verbs) < 5:
            analysis['style_recommendations'].append("Start each bullet point with strong action verbs")
        
        # Check for passive voice
        passive_patterns = [r'\bwas\s+\w+ed\b', r'\bwere\s+\w+ed\b', r'\bbeen\s+\w+ed\b']
        passive_count = sum(len(re.findall(pattern, resume_text.lower())) for pattern in passive_patterns)
        
        if passive_count > 3:
            analysis['style_recommendations'].append("Replace passive voice with active voice (e.g., 'was responsible for' → 'led')")
        
        # Check for vague language
        vague_words = ['various', 'multiple', 'several', 'numerous', 'countless', 'a lot', 'many']
        vague_count = sum(resume_text.lower().count(word) for word in vague_words)
        
        if vague_count > 2:
            analysis['style_recommendations'].append("Replace vague quantifiers with specific numbers (e.g., 'many' → '15+')")
        
        # Check length
        word_count = len(resume_text.split())
        if word_count < 300:
            analysis['weakness_areas'].append("Resume too short - expand with more details and achievements")
        elif word_count > 1000:
            analysis['weakness_areas'].append("Resume too long - focus on most relevant experiences")
        else:
            analysis['strength_areas'].append("Good length for ATS scanning")
        
        # Check for whitespace/structure
        if resume_text.count('\n\n') < 3:
            analysis['style_recommendations'].append("Add clear section breaks for better readability")
        
        return analysis
    
    def _calculate_formatting_score(self, resume_text: str) -> Dict:
        """Calculate formatting score with specific issues"""
        
        issues = []
        score = 0.7  # Base score
        
        # Check for section headers
        sections = ['experience', 'education', 'skills']
        found_sections = sum(1 for section in sections if re.search(r'\b' + section + r'\b', resume_text.lower()))
        
        if found_sections == len(sections):
            score += 0.1
        elif found_sections < 2:
            score -= 0.15
            issues.append("Add clear section headers (Experience, Education, Skills)")
        
        # Check for bullet points
        bullet_count = len(re.findall(r'^[•·●\-]\s', resume_text, re.MULTILINE))
        if bullet_count >= 8:
            score += 0.05
        elif bullet_count < 3:
            score -= 0.1
            issues.append("Use bullet points to highlight achievements")
        
        # Check for consistent formatting
        if re.search(r'\n\s*\n\s*\n', resume_text):
            issues.append("Remove excessive blank lines")
        
        # Check for contact information
        if not re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', resume_text):
            issues.append("Add email address")
            score -= 0.05
        
        if not re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', resume_text):
            issues.append("Add phone number")
            score -= 0.05
        
        return {'score': max(0.4, min(score, 0.95)), 'issues': issues[:5]}
    
    def _calculate_completeness_score(self, resume_data: Dict) -> Dict:
        """Calculate completeness score with specific missing info"""
        
        missing_info = []
        present_count = 0
        total_checks = 7
        
        # Check required sections
        if resume_data.get('personal_info', {}).get('name'):
            present_count += 1
        else:
            missing_info.append("Full name")
        
        if resume_data.get('personal_info', {}).get('email'):
            present_count += 1
        else:
            missing_info.append("Email address")
        
        if resume_data.get('skills') and any(resume_data['skills'].values()):
            present_count += 1
        else:
            missing_info.append("Skills section")
        
        if resume_data.get('experience'):
            present_count += 1
        else:
            missing_info.append("Work experience")
        
        if resume_data.get('education'):
            present_count += 1
        else:
            missing_info.append("Education")
        
        if resume_data.get('projects'):
            present_count += 0.5
        
        if resume_data.get('certifications'):
            present_count += 0.5
        
        score = present_count / total_checks
        
        return {'score': min(score, 0.95), 'missing_info': missing_info[:5]}
    
    def _identify_strengths_weaknesses(self, skills: Dict, experience: Dict, 
                                       impact: Dict, keywords: Dict) -> Tuple[List, List]:
        """Identify key strengths and weaknesses"""
        
        strengths = []
        weaknesses = []
        
        # Skills strengths/weaknesses
        if skills['score'] >= 0.8:
            strengths.append(f"✅ Strong skills alignment: {len(skills['matching'])} matching skills")
            if skills.get('partial_matches'):
                strengths.append(f"🔄 Close skill matches: {len(skills['partial_matches'])} related skills")
        elif skills['score'] < 0.5:
            weaknesses.append(f"⚠️ Missing key skills: {', '.join(skills['missing'][:3])}")
        
        # Experience strengths/weaknesses
        if experience['score'] >= 0.8:
            if experience.get('relevant_years', 0) > 0:
                strengths.append(f"💼 Relevant experience: {experience['relevant_years']:.0f} years in target role")
            else:
                strengths.append(f"💼 Solid experience: {experience['total_years']:.0f} years total")
        elif experience['score'] < 0.5:
            weaknesses.append(f"⚠️ Experience gap: Need {experience['required_years'] - experience['total_years']:.0f} more years")
        
        # Impact metrics strengths/weaknesses
        if impact['score'] >= 0.7:
            strengths.append(f"📊 Strong metrics: {impact['total_metrics']} quantifiable achievements")
        elif impact['score'] < 0.4:
            weaknesses.append("📈 Add more numbers and metrics to showcase impact")
        
        # Keyword strengths
        if keywords['score'] >= 0.7:
            strengths.append(f"🔑 Good keyword optimization: {len(keywords['matching'])} key terms matched")
        
        return strengths[:5], weaknesses[:5]
    
    def _generate_improvement_plan(self, skills: Dict, impact: Dict, keywords: Dict,
                                   restructuring: Dict, number_suggestions: List,
                                   section_rewrites: Dict, quality: Dict) -> Dict:
        """Generate actionable improvement plan"""
        
        improvements = {
            'critical': [],
            'important': [],
            'nice_to_have': [],
            'quick_wins': [],
            'estimated_impact': {}
        }
        
        # Critical improvements (score < 0.5)
        if skills['score'] < 0.5:
            improvements['critical'].append({
                'area': 'Skills Gap',
                'action': f"Add missing key skills: {', '.join(skills['missing'][:3])}",
                'effort': 'Medium',
                'impact': 'High'
            })
        
        if impact['score'] < 0.4:
            improvements['critical'].append({
                'area': 'Missing Metrics',
                'action': 'Add quantifiable achievements with specific numbers and percentages',
                'effort': 'Medium',
                'impact': 'Very High'
            })
        
        # Important improvements
        if keywords['score'] < 0.6:
            improvements['important'].append({
                'area': 'Keyword Optimization',
                'action': f"Include these keywords: {', '.join(keywords['missing'][:5])}",
                'effort': 'Low',
                'impact': 'High'
            })
        
        # Quick wins
        if number_suggestions:
            improvements['quick_wins'].append({
                'action': 'Add specific numbers to experience bullet points',
                'examples': [s.get('example', '') for s in number_suggestions[:2] if s.get('example')]
            })
        
        if quality.get('style_recommendations'):
            improvements['quick_wins'].append({
                'action': quality['style_recommendations'][0],
                'effort': 'Low',
                'impact': 'Medium'
            })
        
        # Restructuring improvements
        if restructuring.get('new_sections'):
            improvements['important'].append({
                'area': 'Section Structure',
                'action': f"Add {restructuring['new_sections'][0]['section']} section",
                'effort': 'Low',
                'impact': 'High'
            })
        
        # Estimate impact for each category
        improvements['estimated_impact'] = {
            'critical': '+15-25%',
            'important': '+10-15%',
            'quick_wins': '+5-10%',
            'total_potential': '+30-50%'
        }
        
        return improvements
    
    def _generate_section_suggestions(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Generate section-specific suggestions"""
        
        suggestions = {
            'skills': [],
            'experience': [],
            'summary': [],
            'education': [],
            'projects': []
        }
        
        # Skills section suggestions
        if resume_data.get('skills'):
            skills_dict = resume_data['skills']
            total_skills = sum(len(v) for v in skills_dict.values() if isinstance(v, list))
            if total_skills < 10:
                suggestions['skills'].append("Expand skills section with more relevant technical skills")
            elif total_skills > 30:
                suggestions['skills'].append("Focus on most relevant skills, remove redundant entries")
        
        # Experience section suggestions
        experiences = resume_data.get('experience', [])
        if len(experiences) < 2:
            suggestions['experience'].append("Add more work experience or expand current roles with details")
        
        for exp in experiences[:2]:
            responsibilities = exp.get('responsibilities', [])
            if responsibilities and len(responsibilities[0]) < 50:
                suggestions['experience'].append(f"In {exp.get('title', 'Role')}, add more detail and metrics")
        
        # Summary section suggestions
        if not resume_data.get('personal_info', {}).get('summary'):
            suggestions['summary'].append("Add a professional summary highlighting key strengths")
        
        return suggestions
    
    def _check_spelling_errors(self, text: str) -> List[Dict]:
        """Check for common spelling errors"""
        common_errors = {
            'recieve': 'receive',
            'acheive': 'achieve',
            'comittment': 'commitment',
            'maintainance': 'maintenance',
            'managment': 'management',
            'developement': 'development',
            'environement': 'environment',
            'implemention': 'implementation',
            'collaboration': 'collaboration',  # Correct spelling
            'seperate': 'separate',
            'definately': 'definitely',
            'occured': 'occurred',
            'priviledge': 'privilege',
            'responsability': 'responsibility'
        }
        
        errors = []
        text_lower = text.lower()
        
        for wrong, correct in common_errors.items():
            if wrong in text_lower:
                errors.append({
                    'word': wrong,
                    'suggestion': correct,
                    'context': self._get_context(text, wrong, 5)
                })
        
        return errors[:5]
    
    def _check_grammar_issues(self, text: str) -> List[Dict]:
        """Check common grammar issues"""
        issues = []
        
        # Check for passive voice
        passive = re.findall(r'\b(?:was|were|is|are|be|been)\s+(\w+ed)\b', text.lower())
        if len(passive) > 3:
            issues.append({
                'type': 'Passive Voice',
                'suggestion': 'Use active voice for stronger impact',
                'example': 'Instead of "was responsible for managing", write "managed"'
            })
        
        # Check for tense inconsistency
        past_tense = len(re.findall(r'\b\w+ed\b', text))
        present_tense = len(re.findall(r'\b(?:manage|lead|develop|create|design)\b', text))
        
        if past_tense > 0 and present_tense > 5:
            issues.append({
                'type': 'Tense Inconsistency',
                'suggestion': 'Use past tense for previous roles, present tense for current role',
                'example': 'Consistently use past tense (-ed) for past experiences'
            })
        
        return issues[:3]
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity ratio"""
        if not str1 or not str2:
            return 0
        
        # Simple Jaccard similarity for words
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0
    
    def _get_context(self, text: str, word: str, window: int = 10) -> str:
        """Get context around a word"""
        words = text.split()
        for i, w in enumerate(words):
            if word in w.lower():
                start = max(0, i - window)
                end = min(len(words), i + window + 1)
                return ' '.join(words[start:end])
        return ""
    
    def _log_scores(self, scores: Dict):
        """Log all scores for debugging"""
        logger.info("-" * 50)
        for name, score in scores.items():
            logger.info(f"{name:20} : {score*100:6.1f}%")
        logger.info("-" * 50)
    
    def _generate_detailed_feedback(self, overall_score: float, skills: Dict,
                                   experience: Dict, impact: Dict,
                                   strengths: List, weaknesses: List) -> str:
        """Generate detailed human-readable feedback"""
        
        feedback_parts = []
        
        # Overall assessment
        if overall_score >= 85:
            feedback_parts.append("🎉 EXCELLENT! Your resume is highly competitive for this role.")
        elif overall_score >= 70:
            feedback_parts.append("👍 GOOD! Your resume is well-aligned with minor improvements needed.")
        elif overall_score >= 55:
            feedback_parts.append("📈 MODERATE! Some significant improvements will boost your chances.")
        else:
            feedback_parts.append("⚠️ NEEDS WORK! Major improvements recommended for better ATS performance.")
        
        feedback_parts.append(f"\n📊 OVERALL SCORE: {overall_score:.0f}%\n")
        
        # Component breakdown
        feedback_parts.append("📈 COMPONENT BREAKDOWN:")
        feedback_parts.append(f"   • Skills Match: {skills['score']*100:.0f}% - {'✅ Good' if skills['score']>=0.7 else '⚠️ Needs work'}")
        feedback_parts.append(f"   • Experience: {experience['score']*100:.0f}% - {'✅ Good' if experience['score']>=0.7 else '⚠️ Needs work'}")
        feedback_parts.append(f"   • Impact Metrics: {impact['score']*100:.0f}% - {'✅ Strong' if impact['score']>=0.7 else '⚠️ Add numbers'}")
        
        # Key recommendations
        if strengths:
            feedback_parts.append(f"\n💪 STRENGTHS:")
            for strength in strengths[:3]:
                feedback_parts.append(f"   • {strength}")
        
        if weaknesses:
            feedback_parts.append(f"\n⚠️ AREAS TO IMPROVE:")
            for weakness in weaknesses[:3]:
                feedback_parts.append(f"   • {weakness}")
        
        # Next steps
        feedback_parts.append(f"\n🎯 TOP 3 NEXT STEPS:")
        if skills['missing']:
            feedback_parts.append(f"   1. Add missing skills: {', '.join(skills['missing'][:3])}")
        if impact['score'] < 0.6:
            feedback_parts.append(f"   2. Quantify achievements with specific numbers and percentages")
        if skills['score'] < 0.7:
            feedback_parts.append(f"   3. Tailor your resume keywords to match job requirements")
        
        return '\n'.join(feedback_parts)