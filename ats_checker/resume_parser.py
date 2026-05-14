# ============================================================
# ADVANCED HYBRID AI RESUME PARSER
# ============================================================
#
# FEATURES
# ------------------------------------------------------------
# ✅ PDF Parsing using PyMuPDF
# ✅ DOCX Parsing
# ✅ Dynamic Section Detection
# ✅ Fuzzy Matching
# ✅ Local Ollama + Gemma Integration
# ✅ Structured JSON Output
# ✅ Retry + JSON Repair
# ✅ Personal Info Extraction
# ✅ Production Ready
# ✅ Django Compatible
# ✅ NO OCR
# ✅ NO TERMINAL PRINTS
#
# INSTALL
# ------------------------------------------------------------
# pip install pymupdf python-docx rapidfuzz requests
#
# RUN OLLAMA
# ------------------------------------------------------------
# ollama run gemma3:latest
#
# ============================================================

import re
import json
import fitz
import requests
import tempfile
import os

from docx import Document
from rapidfuzz import fuzz

from typing import Dict, Any


# ============================================================
# CONFIG
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL = "gemma3:latest"


# ============================================================
# SECTION ALIASES
# ============================================================

SECTION_ALIASES = {

    "summary": [
        "summary",
        "professional summary",
        "career summary",
        "objective",
        "career objective",
        "profile",
        "about me"
    ],

    "education": [
        "education",
        "academic background",
        "academic qualifications",
        "qualifications"
    ],

    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "internship",
        "internships"
    ],

    "projects": [
        "projects",
        "personal projects",
        "academic projects",
        "key projects"
    ],

    "skills": [
        "skills",
        "technical skills",
        "core skills",
        "technologies",
        "tech stack"
    ],

    "certifications_and_awards": [

        "certifications",
        "certification",

        "awards",
        "award",

        "achievements",
        "achievement",

        "honors",
        "licenses",

        "courses",

        "certifications and awards",
        "awards and certifications",

        "awards achievements and certifications"
    ]
}


# ============================================================
# FILE EXTRACTION
# ============================================================

def extract_pdf_text(path: str):

    text = ""

    doc = fitz.open(path)

    for page in doc:

        page_text = page.get_text()

        if page_text:
            text += page_text + "\n"

    return text


def extract_docx_text(path: str):

    doc = Document(path)

    text = []

    for para in doc.paragraphs:

        if para.text.strip():
            text.append(para.text)

    return "\n".join(text)


def extract_resume_text(path: str):

    if path.endswith(".pdf"):
        return extract_pdf_text(path)

    elif path.endswith(".docx"):
        return extract_docx_text(path)

    raise Exception("Unsupported File Format")


# ============================================================
# DJANGO FILE PARSER
# ============================================================

def parse_uploaded_file(uploaded_file):

    temp_path = None

    try:

        extension = os.path.splitext(uploaded_file.name)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:

            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)

            temp_path = temp_file.name

        text = extract_resume_text(temp_path)

        text = clean_text(text)

        return {
            "success": True,
            "text": text,
            "method": "pymupdf",
            "filename": uploaded_file.name,
            "size": uploaded_file.size
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

    finally:

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text: str):

    text = re.sub(r"\r", "\n", text)

    text = re.sub(r"\n+", "\n", text)

    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_line(line: str):

    line = line.lower().strip()

    line = re.sub(r"[^a-zA-Z& ]", "", line)

    return line.strip()


# ============================================================
# SECTION DETECTION
# ============================================================

def is_section_heading(line: str):

    normalized = normalize_line(line)

    if len(normalized) > 50:
        return None

    for section, aliases in SECTION_ALIASES.items():

        for alias in aliases:

            score = fuzz.ratio(normalized, alias)

            if score > 85:
                return section

    return None


def detect_sections(lines):

    detected = []

    used_sections = set()

    for idx, line in enumerate(lines):

        section = is_section_heading(line)

        if section and section not in used_sections:

            detected.append({
                "section": section,
                "line_index": idx
            })

            used_sections.add(section)

    return detected


# ============================================================
# SPLIT SECTIONS
# ============================================================

def split_sections(lines, detected_sections):

    section_data = {}

    if not detected_sections:
        return section_data

    first_section_start = detected_sections[0]["line_index"]

    section_data["personal_info_raw"] = "\n".join(
        lines[0:first_section_start]
    )

    for i in range(len(detected_sections)):

        current = detected_sections[i]

        start = current["line_index"]

        end = (
            detected_sections[i + 1]["line_index"]
            if i + 1 < len(detected_sections)
            else len(lines)
        )

        content = "\n".join(lines[start:end])

        section_data[current["section"]] = content

    return section_data


# ============================================================
# PERSONAL INFO EXTRACTION
# ============================================================

EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

PHONE_REGEX = r"(\+91[- ]?)?[6-9]\d{9}"

LINKEDIN_REGEX = r"linkedin\.com\/in\/[A-Za-z0-9_-]+"

GITHUB_REGEX = r"github\.com\/[A-Za-z0-9_-]+"


def extract_name(text):

    lines = text.split("\n")

    for line in lines[:5]:

        line = line.strip()

        if (
            len(line.split()) >= 2
            and len(line) < 40
            and not re.search(EMAIL_REGEX, line)
            and not re.search(PHONE_REGEX, line)
        ):

            clean_name = re.sub(r"[^a-zA-Z ]", "", line)

            clean_name = " ".join(clean_name.split())

            return clean_name.title()

    return ""


def extract_personal_info(text):

    email = re.search(EMAIL_REGEX, text)

    phone = re.search(PHONE_REGEX, text)

    linkedin = re.search(LINKEDIN_REGEX, text)

    github = re.search(GITHUB_REGEX, text)

    return {
        "name": extract_name(text),
        "email": email.group() if email else "",
        "phone": phone.group() if phone else "",
        "summary": "",
        "location": {},
        "linkedin": linkedin.group() if linkedin else "",
        "github": github.group() if github else ""
    }


# ============================================================
# OLLAMA CALL
# ============================================================

def call_gemma(prompt, retries=2):

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 800,
            "top_p": 0.9
        }
    }

    for _ in range(retries):

        try:

            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=90
            )

            if response.status_code == 200:

                result = response.json()

                return result.get("response", "")

        except:
            pass

    return ""


# ============================================================
# JSON REPAIR
# ============================================================

def repair_json(text):

    if not text:
        return None

    text = text.strip()

    text = text.replace("```json", "")

    text = text.replace("```", "")

    first_brace = text.find("{")

    first_array = text.find("[")

    if first_array != -1 and (
        first_array < first_brace or first_brace == -1
    ):

        start = first_array

        end = text.rfind("]")

    else:

        start = first_brace

        end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    return text[start:end + 1]


def parse_json_response(response):

    repaired = repair_json(response)

    if not repaired:
        return None

    try:

        return json.loads(repaired)

    except:
        return None


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an expert ATS resume parser.

STRICT RULES:
1. Return ONLY VALID JSON
2. No explanation
3. No markdown
4. No extra text
5. Never hallucinate
6. Preserve exact information
"""


# ============================================================
# PROMPTS
# ============================================================

def build_summary_prompt(text):

    return f"""
{SYSTEM_PROMPT}

Extract professional summary.

FORMAT:
{{
  "summary": ""
}}

TEXT:
{text}
"""


def build_education_prompt(text):

    return f"""
{SYSTEM_PROMPT}

Extract education.

RETURN ARRAY.

FORMAT:
[
  {{
    "degree": "",
    "institution": "",
    "field": "",
    "start_date": "",
    "end_date": "",
    "cgpa": ""
  }}
]

TEXT:
{text}
"""


def build_experience_prompt(text):

    return f"""
{SYSTEM_PROMPT}

Extract experience.

RETURN ARRAY.

FORMAT:
[
  {{
    "title": "",
    "company": "",
    "duration_years": 0,
    "start_date": "",
    "end_date": "",
    "responsibilities": [],
    "achievements": [],
    "technologies": []
  }}
]

TEXT:
{text}
"""


def build_projects_prompt(text):

    return f"""
{SYSTEM_PROMPT}

Extract projects.

RETURN ARRAY.

FORMAT:
[
  {{
    "name": "",
    "description": "",
    "technologies": [],
    "github": ""
  }}
]

TEXT:
{text}
"""


def build_skills_prompt(text):

    return f"""
{SYSTEM_PROMPT}

Extract technical skills.

FORMAT:
{{
  "technical": [],
  "soft": [],
  "tools": [],
  "languages": []
}}

TEXT:
{text}
"""


def build_certifications_prompt(text):

    return f"""
{SYSTEM_PROMPT}

Extract certifications, awards and achievements.

RETURN ARRAY.

FORMAT:
[
  {{
    "title": "",
    "issuer": "",
    "date": "",
    "type": ""
  }}
]

TEXT:
{text}
"""


# ============================================================
# AI EXTRACTION
# ============================================================

def extract_section_with_ai(section, content):

    prompt_map = {

        "summary": build_summary_prompt,

        "education": build_education_prompt,

        "experience": build_experience_prompt,

        "projects": build_projects_prompt,

        "skills": build_skills_prompt,

        "certifications_and_awards":
            build_certifications_prompt
    }

    if section not in prompt_map:
        return None

    prompt = prompt_map[section](content)

    response = call_gemma(prompt)

    parsed = parse_json_response(response)

    return parsed


# ============================================================
# MAIN RESUME PARSER
# ============================================================

class AdvancedResumeParser:

    def __init__(
        self,
        ollama_url="http://localhost:11434",
        model="gemma3:latest",
        use_llm=True
    ):

        self.ollama_url = ollama_url

        self.model = model

        self.use_llm = use_llm

    # ========================================================
    # MAIN RESUME EXTRACTION
    # ========================================================

    def extract_comprehensive_resume_data(
        self,
        resume_text: str
    ) -> Dict[str, Any]:

        cleaned_text = clean_text(resume_text)

        lines = cleaned_text.split("\n")

        detected_sections = detect_sections(lines)

        sections = split_sections(
            lines,
            detected_sections
        )

        result = {

            'personal_info': {
                'name': '',
                'email': '',
                'phone': '',
                'summary': '',
                'location': {},
                'linkedin': '',
                'github': ''
            },

            'skills': {
                'technical': [],
                'soft': [],
                'tools': [],
                'languages': []
            },

            'experience': [],

            'education': [],

            'projects': [],

            'publications': [],

            'achievements': [],

            'volunteering': [],

            'metrics': {
                'total_experience_years': 0,
                'skill_count': 0,
                'total_projects': 0
            }
        }

        # ====================================================
        # PERSONAL INFO
        # ====================================================

        personal_info_raw = sections.get(
            "personal_info_raw",
            ""
        )

        result["personal_info"] = extract_personal_info(
            personal_info_raw
        )

        # ====================================================
        # AI EXTRACTION
        # ====================================================

        for section, content in sections.items():

            if section == "personal_info_raw":
                continue

            extracted = extract_section_with_ai(
                section,
                content
            )

            if not extracted:
                continue

            # =================================================
            # SUMMARY
            # =================================================

            if section == "summary":

                if isinstance(extracted, dict):

                    result["personal_info"]["summary"] = (
                        extracted.get("summary", "")
                    )

            # =================================================
            # EDUCATION
            # =================================================

            elif section == "education":

                if isinstance(extracted, list):

                    result["education"] = extracted

            # =================================================
            # EXPERIENCE
            # =================================================

            elif section == "experience":

                if isinstance(extracted, list):

                    result["experience"] = extracted

            # =================================================
            # PROJECTS
            # =================================================

            elif section == "projects":

                if isinstance(extracted, list):

                    result["projects"] = extracted

            # =================================================
            # SKILLS
            # =================================================

            elif section == "skills":

                if isinstance(extracted, dict):

                    result["skills"] = extracted

            # =================================================
            # CERTIFICATIONS / ACHIEVEMENTS
            # =================================================

            elif section == "certifications_and_awards":

                if isinstance(extracted, list):

                    result["achievements"] = extracted

        # ====================================================
        # METRICS
        # ====================================================

        result["metrics"] = self.calculate_metrics(
            result
        )

        return result

    # ========================================================
    # METRICS
    # ========================================================

    def calculate_metrics(self, result):

        total_experience = 0

        for exp in result.get("experience", []):

            duration = exp.get(
                "duration_years",
                0
            )

            try:
                total_experience += float(duration)
            except:
                pass

        technical_skills = result.get(
            "skills",
            {}
        ).get("technical", [])

        projects = result.get(
            "projects",
            []
        )

        return {
            "total_experience_years":
                total_experience,

            "skill_count":
                len(technical_skills),

            "total_projects":
                len(projects)
        }

    # ========================================================
    # JD PARSER
    # ========================================================

    def extract_comprehensive_jd_data(
        self,
        jd_text: str
    ) -> Dict[str, Any]:

        years_match = re.search(
            r'(\d+)[\+\s]*years?',
            jd_text,
            re.IGNORECASE
        )

        years = int(
            years_match.group(1)
        ) if years_match else 0

        skill_keywords = [
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
            'swift', 'kotlin', 'php', 'scala', 'perl', 'r', 'matlab', 'bash', 'powershell',
            'html', 'css', 'sass', 'less', 'sql', 'nosql',
            
            # Frameworks & Libraries
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'springboot',
            'express', 'nestjs', 'rails', 'laravel', 'asp.net', 'jquery', 'bootstrap',
            'tailwind', 'material-ui', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'keras',
            'scikit-learn', 'selenium', 'cypress', 'jest', 'junit', 'mocha', 'chai',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'sqlite', 'oracle', 'redis', 'cassandra',
            'dynamodb', 'firebase', 'elasticsearch', 'mariadb', 'couchdb', 'neo4j',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'heroku', 'digitalocean', 'linode', 'cloudflare',
            'docker', 'kubernetes', 'jenkins', 'gitlab-ci', 'github-actions', 'circleci',
            'terraform', 'ansible', 'puppet', 'chef', 'prometheus', 'grafana', 'elk',
            'splunk', 'datadog', 'newrelic',
            
            # Version Control & Tools
            'git', 'github', 'gitlab', 'bitbucket', 'svn', 'mercurial',
            'jira', 'confluence', 'trello', 'asana', 'slack', 'teams',
            'postman', 'swagger', 'insomnia', 'soapui', 'figma', 'adobe-xd',
            
            # Testing & QA
            'pytest', 'unittest', 'selenium', 'cypress', 'playwright', 'testcafe',
            'jmeter', 'loadrunner', 'sonarqube', 'owasp', 'burpsuite',
            
            # Soft Skills
            'communication', 'teamwork', 'leadership', 'problemsolving', 'criticalthinking',
            'timemanagement', 'adaptability', 'creativity', 'emotionalintelligence',
            'conflictresolution', 'negotiation', 'presentation', 'publicspeaking',
            'writing', 'documentation', 'mentoring', 'coaching', 'collaboration',
            'organization', 'planning', 'prioritization', 'multitasking', 'attentiontodetail',
            'analytical', 'research', 'decisionmaking', 'delegation', 'feedback',
            'interpersonal', 'listening', 'empathy', 'patience', 'flexibility',
            'resilience', 'initiative', 'proactive', 'selfmotivated', 'reliable',
            'dependable', 'punctual', 'ethical', 'integrity', 'professionalism',
            
            # Business & Management
            'agile', 'scrum', 'kanban', 'waterfall', 'projectmanagement', 'productmanagement',
            'businessanalysis', 'requirementsgathering', 'usertesting', 'qa', 'qualityassurance',
            'riskmanagement', 'stakeholdermanagement', 'vendor management', 'budgeting',
            'forecasting', 'analytics', 'metricstracking', 'kpi', 'okr', 'roadmap',
            
            # Design & Creative
            'ui', 'ux', 'userexperience', 'userinterface', 'wireframing', 'prototyping',
            'photoshop', 'illustrator', 'indesign', 'aftereffects', 'premiere-pro',
            'blender', 'maya', '3dsmax', 'autocad', 'sketch', 'invision', 'zeplin',
            
            # Data Science & AI
            'machinelearning', 'deeplearning', 'nlp', 'computervision', 'reinforcementlearning',
            'datamining', 'datavisualization', 'tableau', 'powerbi', 'looker', 'metabase',
            'hadoop', 'spark', 'kafka', 'airflow', 'dbt', 'airbyte',
            
            # Mobile Development
            'android', 'ios', 'reactnative', 'flutter', 'xamarin', 'ionic', 'cordova',
            'swiftui', 'uikit', 'jetpackcompose', 'kotlin', 'androidstudio', 'xcode'
        ]

        required_skills = []

        text_lower = jd_text.lower()

        for skill in skill_keywords:

            if skill in text_lower:
                required_skills.append(skill)

        title = ""

        for line in jd_text.split("\n")[:5]:

            if line.strip():

                title = line.strip()

                break

        return {

            'job_metadata': {
                'title': title,
                'company': '',
                'location': '',
                'job_type': '',
                'experience_level': ''
            },

            'requirements': {

                'must_have': {

                    'skills': [

                        {
                            'name': s,
                            'level': '',
                            'years': 0
                        }

                        for s in required_skills
                    ],

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

                'technical_keywords':
                    required_skills,

                'soft_skills_keywords': [],

                'industry_keywords': []
            },

            'role_context': {}
        }