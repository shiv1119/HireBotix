# ============================================================
# ADVANCED AI RESUME PARSER PIPELINE
# ============================================================
#
# FEATURES
# ------------------------------------------------------------
# 1. PDF + DOCX Parsing
# 2. Dynamic Resume Section Detection
# 3. Fuzzy Matching for Headings
# 4. Smart Personal Info Extraction
# 5. AI Extraction using Ollama + Gemma
# 6. Retry + JSON Repair
# 7. Structured Resume JSON
# 8. Supports Any Resume Format
# 9. Handles Broken AI Responses
# 10. Better Name Detection
# 11. Better Section Boundary Detection
# 12. Better Prompt Engineering
# 13. Combined Awards + Certifications Section
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

from docx import Document
from rapidfuzz import fuzz

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
        "profile",
        "objective",
        "career objective",
        "about me"
    ],

    "education": [
        "education",
        "academic background",
        "academic qualification",
        "qualifications",
        "studies"
    ],

    "experience": [
        "experience",
        "work experience",
        "employment history",
        "professional experience",
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

    # ========================================================
    # COMBINED CERTIFICATIONS + ACHIEVEMENTS
    # ========================================================

    "certifications_and_awards": [

        "certifications",
        "certification",

        "awards",
        "award",

        "achievements",
        "achievement",

        "honors",
        "honour",

        "licenses",
        "courses",

        "awards and certifications",
        "awards & certifications",

        "certifications and awards",
        "certifications & awards",

        "achievements and certifications",
        "certifications and achievements",

        "awards achievements and certifications",

        "licenses and certifications",

        "honors and awards",

        "certifications achievements awards"
    ]
}

# ============================================================
# FILE EXTRACTION
# ============================================================

def extract_pdf_text(path: str):

    text = ""

    doc = fitz.open(path)

    for page in doc:
        text += page.get_text()

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

    else:
        raise Exception("Unsupported File Format")


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

        if section:

            if section not in used_sections:

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

    # ========================================================
    # PERSONAL INFO
    # ========================================================

    first_section_start = detected_sections[0]["line_index"]

    section_data["personal_info_raw"] = "\n".join(
        lines[0:first_section_start]
    )

    # ========================================================
    # OTHER SECTIONS
    # ========================================================

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

    return None


def extract_personal_info(text):

    email = re.search(EMAIL_REGEX, text)

    phone = re.search(PHONE_REGEX, text)

    linkedin = re.search(LINKEDIN_REGEX, text)

    github = re.search(GITHUB_REGEX, text)

    return {
        "name": extract_name(text),
        "email": email.group() if email else None,
        "phone": phone.group() if phone else None,
        "linkedin": linkedin.group() if linkedin else None,
        "github": github.group() if github else None
    }


# ============================================================
# OLLAMA CALL
# ============================================================

def call_gemma(prompt, retries=3):

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    for attempt in range(retries):

        try:

            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=120
            )

            result = response.json()

            return result["response"]

        except Exception as e:

            print(f"Retry {attempt + 1} Failed:", e)

    return None


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

    except Exception as e:

        print("\nJSON PARSE ERROR")

        print(e)

        return None


# ============================================================
# PROMPTS
# ============================================================

SYSTEM_PROMPT = """
You are an expert ATS resume parser.

STRICT RULES:
1. Return ONLY valid JSON
2. No explanation
3. No markdown
4. No extra text
5. Preserve original information
6. Never hallucinate
7. Use arrays properly
"""


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

Extract education details.

RETURN JSON ARRAY.

FIELDS:
- degree
- institution
- start_date
- end_date
- cgpa

TEXT:
{text}
"""


def build_experience_prompt(text):

    return f"""
{SYSTEM_PROMPT}

Extract work experience.

RETURN JSON ARRAY.

FIELDS:
- company
- role
- start_date
- end_date
- responsibilities
- technologies

TEXT:
{text}
"""


def build_projects_prompt(text):

    return f"""
{SYSTEM_PROMPT}

Extract projects.

RETURN JSON ARRAY.

FIELDS:
- name
- description
- technologies
- github

TEXT:
{text}
"""


def build_skills_prompt(text):

    return f"""
{SYSTEM_PROMPT}

Extract technical skills.

FORMAT:
{{
  "languages": [],
  "frameworks": [],
  "databases": [],
  "cloud": [],
  "tools": []
}}

TEXT:
{text}
"""


# ============================================================
# COMBINED CERTIFICATIONS + AWARDS PROMPT
# ============================================================

def build_certifications_and_awards_prompt(text):

    return f"""
{SYSTEM_PROMPT}

Extract certifications, awards, achievements,
honors, licenses, and courses.

RETURN JSON ARRAY.

FORMAT:
[
  {{
    "title": "",
    "issuer": "",
    "date": "",
    "type": ""
  }}
]

RULES:
- type can be:
  certification
  award
  achievement
  honor
  course
  license

TEXT:
{text}
"""


# ============================================================
# AI EXTRACTION
# ============================================================

def extract_section_with_ai(section, content):

    print(f"\nPROCESSING SECTION: {section}")

    prompt_map = {

        "summary": build_summary_prompt,

        "education": build_education_prompt,

        "experience": build_experience_prompt,

        "projects": build_projects_prompt,

        "skills": build_skills_prompt,

        "certifications_and_awards":
            build_certifications_and_awards_prompt
    }

    if section not in prompt_map:
        return None

    prompt = prompt_map[section](content)

    response = call_gemma(prompt)

    parsed = parse_json_response(response)

    return parsed


# ============================================================
# MAIN PIPELINE
# ============================================================

def process_resume(path):

    print("=" * 60)

    print("READING RESUME")

    print("=" * 60)

    raw_text = extract_resume_text(path)

    cleaned_text = clean_text(raw_text)

    lines = cleaned_text.split("\n")

    # ========================================================
    # DETECT SECTIONS
    # ========================================================

    print("=" * 60)

    print("DETECTING SECTIONS")

    print("=" * 60)

    detected_sections = detect_sections(lines)

    print(json.dumps(detected_sections, indent=4))

    # ========================================================
    # SPLIT SECTIONS
    # ========================================================

    print("=" * 60)

    print("SPLITTING SECTIONS")

    print("=" * 60)

    sections = split_sections(lines, detected_sections)

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    final_output = {

        "personal_info": {},

        "summary": {},

        "education": [],

        "experience": [],

        "projects": [],

        "skills": {},

        "certifications_and_awards": []
    }

    # ========================================================
    # PERSONAL INFO
    # ========================================================

    personal_info_raw = sections.get(
        "personal_info_raw",
        ""
    )

    final_output["personal_info"] = extract_personal_info(
        personal_info_raw
    )

    # ========================================================
    # AI EXTRACTION
    # ========================================================

    for section, content in sections.items():

        if section == "personal_info_raw":
            continue

        extracted = extract_section_with_ai(
            section,
            content
        )

        if extracted:

            final_output[section] = extracted

    return final_output


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    resume_path = "./media/resumes/Shiv_Nandan_Verma_Resume_Fullstack.pdf"

    result = process_resume(resume_path)

    print("\n" + "=" * 60)

    print("FINAL STRUCTURED JSON")

    print("=" * 60)

    print(json.dumps(result, indent=4))