VACANCY_ANALYSIS_PROMPT = """
    Analyze the following job vacancy description and extract the specified parameters.
    Provide the result as a JSON object with the exact keys listed below.
    If a parameter cannot be determined or is not mentioned, leave its value as null or an empty list/object.

    Parameters to extract:
    1. skills: Array of strings. Key technical skills,  technologies, specific tools, and competencies mentioned (e.g., ["Python", "Django", "Git", "Docker", "AWS", "REST API"]).
    2. languages: Array of objects. Languages required, including proficiency level if mentioned. Format: [{{"language": "English", "level": "B2"}}, ...]. If no level, use null for level.
    3. location: String. The candidate's location mentioned (e.g., "Kyiv", "Lviv", "Odesa"). Only city/town here, do not add area or country!
    4. salary_range: String. The salary range mentioned, in the format "min-max currency" (e.g., "50000-70000 UAH", "60000 EUR"). If not specified, null.
    5. level: String. The experience level required (e.g., "Junior", "Middle", "Senior", "Lead"). If not specified, null.
    6. english_level: String. The required English proficiency level (e.g., "A1", "A2", "B1", "B2", "C1", "C2"). If not specified, null.
    7. is_remote: Boolean. Is the position fully remote? (true/false). If not specified or unclear, null.
    8. is_hybrid: Boolean. Is the position hybrid (mix of remote/office)? (true/false). If not specified or unclear, null.
    9. willing_to_relocate: Boolean. Is the candidate expected to relocate? (true/false). If not specified or unclear, null.
    10. responsibilities: Array of strings. Key responsibilities listed (e.g., ["Develop web applications", "Write unit tests"]).

    Job Description:
    {vacancy_text}

    JSON Output:
    """

CV_ANALYSIS_PROMPT = """
Analyze the following candidate resume/CV and extract the specified parameters.
Provide the result as a JSON object with the exact keys listed below.
If a parameter cannot be determined or is not mentioned, leave its value as null or an empty list/object.

Parameters to extract:
1. skills: Array of strings. Key technical skills,  technologies, specific tools, and competencies mentioned (e.g., ["Python", "Django", "Git", "Docker", "AWS", "REST API"]).
2. languages: Array of objects. Languages mentioned, including proficiency level if mentioned. Format: [{{"language": "English", "level": "B2"}}, ...]. If no level, use null for level.
3. location: String. The candidate's location mentioned (e.g., "Kyiv", "Lviv", "Odesa").  Only city/town here, do not add area or country!
4. salary_range: String. The candidate's expected salary range mentioned, in the format "min-max currency" (e.g., "50000-70000 UAH", "60000 EUR", "Negotiable"). If not specified, null.
5. level: String. The candidate's experience level implied (e.g., "Junior", "Middle", "Senior", "Lead"). If not specified, null.
6. english_level: String. The candidate's stated or implied English proficiency level (e.g., "A1", "A2", "B1", "B2", "C1", "C2"). If not specified, null.
7. is_remote: Boolean. Is the candidate open to remote work? (true/false). If not specified or unclear, null.
8. is_hybrid: Boolean. Is the candidate open to hybrid work? (true/false). If not specified or unclear, null.
9. willing_to_relocate: Boolean. Is the candidate willing to relocate? (true/false). If not specified or unclear, null.
10. responsibilities: Array of strings. Key responsibilities or achievements listed in previous roles (e.g., ["Developed web applications", "Led a team of 5 developers"]).

Candidate Resume/CV Text:
{cv_text}

JSON Output:
"""
