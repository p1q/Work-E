VACANCY_ANALYSIS_PROMPT = """
    Analyze the following job vacancy text and extract the specified parameters.
    Provide the result as a JSON object with the exact keys listed below.
    If a parameter cannot be determined or is not mentioned, leave its value as null or an empty list/object or as explicitly stated.
    If the vacancy is written in a language other than English, it must be translated into English and returned in its entirety in English!

    Parameters to extract:
    1. title: String. Title of the vacancy. If not specified, come up with a short one.
    2. link: String. Link to the vacancy on a website. If not specified, null.
    3. level: String. The experience level required (e.g., "Junior", "Middle", "Senior", "Lead"). If not specified, null.
    4. categories: Array of strings. Only one main category to which this vacancy can be assigned (e.g., ["Java", "DevOps"]).
    5. countries: Array of strings. Which countries are candidates considered from? If not specified, null.
    6. cities: Array of strings. Which cities are candidates considered from? (e.g., "Kyiv", "Lviv", "Odesa"). Only cities/towns here, do not add area or country! If not specified, null.
    7. is_remote: Boolean. Is the position fully remote? (true/false). If not specified or unclear, null. A vacancy cannot be both fully remote and hybrid at the same time!
    8. is_hybrid: Boolean. Is the position hybrid (mix of remote/office)? (true/false). If not specified or unclear, null. A vacancy cannot be both fully remote and hybrid at the same time!
    9. languages: Array of objects. Languages required, including proficiency level if mentioned. Format: [{{"language": "English", "level": "B2"}}, ...]. Available options: "A1", "A2", "B1", "B2", "C1", "C2". If no level, use null for level.
    10. skills: Array of strings. Key technical skills,  technologies, specific tools, and competencies mentioned (e.g., ["Python", "Django", "Git", "Docker", "AWS", "REST API"]).
    11. description: String. Description of the vacancy. If not specified, null.
    12. salary_min: Positive Integer. Minimum salary amount (e.g. 50000). If not specified, null.
    13. salary_max: Positive Integer. Maximum salary amount (e.g. 70000). If not specified, null.
    14. salary_currency: String. Currency of salary (e.g., "UAH", "EUR"). If not specified, null.

    Job Original Text:
    {vacancy_text}

    JSON Output:
    """

CV_ANALYSIS_PROMPT = """
    Analyze the following candidate resume/CV and extract the specified parameters.
    Provide the result as a JSON object with the exact keys listed below.
    If a parameter cannot be determined or is not mentioned, leave its value as null or an empty list/object.
    If the CV is written in a language other than English, translate it into English and return the entire output in English.
    
    Parameters to extract:
    1. level: String. The candidate's experience level implied (Available options: "Trainee", "Junior", "Middle", "Senior", "Lead", "C-Level"). If not specified, null.
    2. categories: Array of strings. Only one main professional category (e.g., ["Python"], ["Product Manager"]). If not specified, [].
    3. countries: Array of strings. Countries the candidate is open to working in (e.g., ["Ukraine", "Poland"]). If not specified, [].
    4. cities: Array of strings. Cities the candidate is open to working in (e.g., ["Kyiv", "Lviv"]). Only city names. If not specified, [].
    5. is_office: Boolean. Does the candidate accept full-time office work? If not mentioned, null.
    6. is_remote: Boolean. Does the candidate accept fully remote work? If not mentioned, null.
    7. is_hybrid: Boolean. Does the candidate accept hybrid work? If not mentioned, null.
    8. willing_to_relocate: Boolean. Is the candidate willing to relocate? If not mentioned, null.
    9. languages: Array of objects. Format: [{{"language": "English", "level": "B2"}}, ...]. Valid levels: "A1", "A2", "B1", "B2", "C1", "C2", "native". If level unknown, omit or use null.
    10. skills: Array of strings. Technical skills only (e.g., ["Python", "Django", "Docker"]). Do not include soft skills. If none, [].
    11. salary_min: Positive integer. Minimum expected salary. If not specified, null.
    12. salary_max: Positive integer. Maximum expected salary. If not specified, null.
    13. salary_currency: String. Currency code (e.g., "UAH", "USD"). If not specified, null.
    
    Important:
    - Return ONLY valid JSON.
    - Do NOT include markdown, code fences, or extra text.
    - All string values must be in English.
    
    Candidate Resume/CV Text:
    {cv_text}
    
    JSON Output:
    """
