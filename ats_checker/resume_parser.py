import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import tempfile
import os
import re

# =========================
# CONFIG (WINDOWS PATHS)
# =========================
POPPLER_PATH = r"C:\poppler\poppler-25.12.0\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# =========================
# METHOD 1: PDFPLUMBER
# =========================
def extract_with_pdfplumber(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print("PDFPlumber Error:", e)
    return text


# =========================
# METHOD 2: OCR (FIXED)
# =========================
def extract_with_ocr(file_path):
    text = ""
    try:
        images = convert_from_path(
            file_path,
            poppler_path=POPPLER_PATH  # ✅ FIXED HERE
        )

        for img in images:
            page_text = pytesseract.image_to_string(img)
            text += page_text + "\n"

    except Exception as e:
        print("OCR Error:", e)

    return text


# =========================
# CLEAN TEXT
# =========================
def clean_text(text):
    # Preserve line breaks, only clean spaces
    text = re.sub(r'[ \t]+', ' ', text)   # remove extra spaces but NOT newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)  # normalize empty lines
    return text.strip()


def parse_uploaded_file(uploaded_file):
    """
    Main function to handle uploaded PDF in Django
    """

    temp_path = None

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name

        # =========================
        # STEP 1: Try PDFPlumber
        # =========================
        text = extract_with_pdfplumber(temp_path)
        method = "pdfplumber"

        # =========================
        # STEP 2: Fallback to OCR
        # =========================
        if len(text.strip()) < 50:
            print("⚠️ Using OCR fallback...")
            text = extract_with_ocr(temp_path)
            method = "ocr"

        # =========================
        # CLEAN TEXT
        # =========================
        text = clean_text(text)

        return {
            "success": True,
            "text": text,
            "method": method,
            "filename": uploaded_file.name,
            "size": uploaded_file.size
        }

    except Exception as e:
        print("Parsing Error:", e)
        return {
            "success": False,
            "error": str(e)
        }

    finally:
        # Cleanup temp file safely
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# resume_parser.py - Fixed version ensuring proper dict structures

import json
import re
import requests
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AdvancedResumeParser:
    """
    Resume parser with fallback to avoid timeouts
    """
    
    def __init__(self, ollama_url="http://localhost:11434", model="gemma3", use_llm=False):
        self.ollama_url = ollama_url
        self.model = model
        self.use_llm = use_llm
    
    def _call_gemma(self, prompt: str, max_retries: int = 1) -> str:
        """Call local Gemma model - skip if use_llm is False"""
        if not self.use_llm:
            return ""
            
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 500,
                            "top_p": 0.9,
                            "num_ctx": 1024
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    return response.json().get("response", "")
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                
        return ""
    
    def extract_comprehensive_resume_data(self, resume_text: str) -> Dict[str, Any]:
        """Extract structured information from resume"""
        
        if self.use_llm:
            prompt = f"""Extract from resume. Return ONLY JSON with: name, email, phone, skills, experience, education.
Resume: {resume_text[:4000]}
JSON format: {{"personal_info":{{"name":"","email":""}},"skills":{{"technical":[]}},"experience":[],"education":[]}}"""
            
            response = self._call_gemma(prompt)
            if response:
                try:
                    response = re.sub(r'```json\s*', '', response)
                    response = re.sub(r'```\s*', '', response)
                    result = json.loads(response.strip())
                    # Ensure result is a dict
                    if isinstance(result, dict):
                        return self._ensure_resume_structure(result)
                except:
                    pass
        
        return self._extract_with_regex(resume_text)
    
    def extract_comprehensive_jd_data(self, jd_text: str) -> Dict[str, Any]:
        """Extract structured information from job description"""
        
        if self.use_llm:
            prompt = f"""Extract from job description. Return ONLY JSON with: title, required_skills, experience_years.
JD: {jd_text[:4000]}
JSON: {{"job_metadata":{{"title":""}},"qualifications":{{"required_skills":[],"min_experience_years":0}},"requirements":{{"must_have":{{"skills":[]}}}}}}"""
            
            response = self._call_gemma(prompt)
            if response:
                try:
                    response = re.sub(r'```json\s*', '', response)
                    response = re.sub(r'```\s*', '', response)
                    result = json.loads(response.strip())
                    if isinstance(result, dict):
                        return self._ensure_jd_structure(result)
                except:
                    pass
        
        return self._extract_jd_with_regex(jd_text)
    
    def _ensure_resume_structure(self, data: Dict) -> Dict:
        """Ensure resume data has all required fields as dicts, not lists"""
        return {
            'personal_info': data.get('personal_info', {}) if isinstance(data.get('personal_info'), dict) else {},
            'skills': data.get('skills', {}) if isinstance(data.get('skills'), dict) else {'technical': [], 'soft': [], 'tools': []},
            'experience': data.get('experience', []) if isinstance(data.get('experience'), list) else [],
            'education': data.get('education', []) if isinstance(data.get('education'), list) else [],
            'projects': data.get('projects', []) if isinstance(data.get('projects'), list) else [],
            'metrics': data.get('metrics', {}) if isinstance(data.get('metrics'), dict) else {}
        }
    
    def _ensure_jd_structure(self, data: Dict) -> Dict:
        """Ensure JD data has all required fields as dicts, not lists"""
        return {
            'job_metadata': data.get('job_metadata', {}) if isinstance(data.get('job_metadata'), dict) else {},
            'requirements': data.get('requirements', {}) if isinstance(data.get('requirements'), dict) else {'must_have': {}, 'nice_to_have': {}},
            'responsibilities': data.get('responsibilities', []) if isinstance(data.get('responsibilities'), list) else [],
            'qualifications': data.get('qualifications', {}) if isinstance(data.get('qualifications'), dict) else {},
            'keywords_analysis': data.get('keywords_analysis', {}) if isinstance(data.get('keywords_analysis'), dict) else {}
        }
    
    def _extract_with_regex(self, text: str) -> Dict:
        """Extract basic info using regex patterns - returns proper dict structure"""
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = email_match.group(0) if email_match else ""
        
        # Extract phone
        phone_match = re.search(r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{4}', text)
        phone = phone_match.group(0) if phone_match else ""
        
        # Extract name
        lines = text.split('\n')
        name = ""
        for line in lines[:5]:
            if line.strip() and not any(x in line.lower() for x in ['email', 'phone', 'resume']):
                words = line.strip().split()
                if len(words) <= 4 and all(w and w[0].isupper() for w in words if w):
                    name = line.strip()
                    break
        
        # Extract skills
        skill_keywords = ['python', 'java', 'javascript', 'react', 'django', 'sql', 'aws', 'docker', 
                          'git', 'html', 'css', 'node', 'angular', 'vue', 'mongodb', 'postgresql']
        
        skills = []
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                skills.append({'name': skill, 'level': 'unknown'})
        
        # Extract experience
        experience = []
        date_pattern = r'\b(19|20)\d{2}\b'
        dates = re.findall(date_pattern, text)
        years_count = len(set(dates))
        
        if years_count > 0:
            experience.append({
                'title': 'Work Experience',
                'company': '',
                'duration_years': years_count,
                'responsibilities': [],
                'achievements': []
            })
        
        # Extract education
        education = []
        degree_keywords = ['bachelor', 'master', 'phd', 'bs', 'ms', 'bsc', 'msc', 'degree']
        for keyword in degree_keywords:
            if keyword in text_lower:
                education.append({
                    'degree': keyword.upper(),
                    'institution': '',
                    'field': '',
                    'start_date': '',
                    'end_date': ''
                })
                break
        
        return {
            'personal_info': {
                'name': name,
                'email': email,
                'phone': phone,
                'summary': text[:300],
                'location': {},
                'linkedin': '',
                'github': ''
            },
            'skills': {
                'technical': skills,
                'soft': [],
                'tools': [],
                'languages': []
            },
            'experience': experience,
            'education': education,
            'projects': [],
            'publications': [],
            'achievements': [],
            'volunteering': [],
            'metrics': {
                'total_experience_years': years_count,
                'skill_count': len(skills),
                'total_projects': 0
            }
        }
    
    def _extract_jd_with_regex(self, text: str) -> Dict:
        """Extract JD info using regex - returns proper dict structure"""
        
        # Extract title
        lines = text.split('\n')
        title = ""
        for line in lines[:3]:
            if line.strip():
                title = line.strip()[:100]
                break
        
        # Extract company
        company = ""
        for line in lines[:5]:
            if 'company' in line.lower() or 'at ' in line.lower():
                company = line.strip()
                break
        
        # Extract years requirement
        years_match = re.search(r'(\d+)[\+\s]*years?', text, re.IGNORECASE)
        years = int(years_match.group(1)) if years_match else 0
        
        # Extract skills
        skill_keywords = ['python', 'java', 'javascript', 'react', 'django', 'sql', 'aws', 'docker',
                          'git', 'html', 'css', 'node', 'angular', 'vue', 'mongodb', 'postgresql']
        required_skills = []
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                required_skills.append(skill)
        
        return {
            'job_metadata': {
                'title': title,
                'company': company,
                'location': '',
                'job_type': '',
                'experience_level': ''
            },
            'requirements': {
                'must_have': {
                    'skills': [{'name': s, 'level': '', 'years': 0} for s in required_skills],
                    'experience': [],
                    'education': []
                },
                'nice_to_have': {
                    'skills': [],
                    'experience': [],
                    'education': []
                }
            },
            'responsibilities': [],
            'qualifications': {
                'min_education': '',
                'min_experience_years': years,
                'preferred_experience_years': years,
                'required_skills': required_skills,
                'preferred_skills': []
            },
            'company_info': {},
            'keywords_analysis': {
                'technical_keywords': required_skills,
                'soft_skills_keywords': [],
                'industry_keywords': []
            },
            'role_context': {}
        }