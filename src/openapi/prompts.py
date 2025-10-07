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
    1. personal: Object. Personal information structure:
       {{
           "first_name": "string",
           "last_name": "string", 
           "email": "string (email format)",
           "phone": "string (E.164 format, optional)",
           "date_of_birth": "YYYY-MM-DD (optional)",
           "gender": "string (optional)",
           "address": {{
               "street": "string (optional)",
               "city": "string (optional)",
               "postal_code": "string (optional)",
               "country": "string (optional)"
           }},
           "overview": "string (optional, max 2000 chars)",
           "hobbies": "string (optional, max 1000 chars)"
       }}
    2. position_target: String. Target position. If not specified, null.
    3. work_experiences: Array of objects. Work history:
       [
           {{
               "position": "string (1-120 chars)",
               "company": "string (1-120 chars)",
               "start_date": "YYYY-MM",
               "end_date": "YYYY-MM (null if current)",
               "is_current": "boolean (true if end_date is null)",
               "responsibilities": "string (optional)",
               "order_index": "integer (for sorting)"
           }}
       ]
    4. work_options: Object. Work preferences:
       {{
           "countries": ["string"],
           "cities": ["string"], 
           "is_office": "boolean (optional)",
           "is_remote": "boolean (optional)",
           "is_hybrid": "boolean (optional)",
           "willing_to_relocate": "boolean (optional)"
       }}
    5. educations: Array of objects. Education history:
       [
           {{
               "major": "string",
               "institution": "string",
               "start_date": "YYYY-MM",
               "end_date": "YYYY-MM (null if current)",
               "description": "string (optional)",
               "order_index": "integer (for sorting)"
           }}
       ]
    6. courses: Array of objects. Course history:
       [
           {{
               "name": "string",
               "provider": "string",
               "start_date": "YYYY-MM", 
               "end_date": "YYYY-MM (null if current)",
               "description": "string (optional)",
               "order_index": "integer (for sorting)"
           }}
       ]
    7. skills: Array of objects. Skills with levels:
       [
           {{
               "name": "string",
               "description": "string (optional)",
               "level": "string (basic|intermediate|advanced|expert|null, optional)",
               "order_index": "integer (for sorting)"
           }}
       ]
    8. languages: Array of objects. Language proficiency:
       [
           {{
               "name": "string",
               "level": "string (A1|A2|B1|B2|C1|C2|native, optional)",
               "description": "string (optional)",
               "order_index": "integer (for sorting)"
           }}
       ]
    9. links: Object. URLs:
       {{
           "linkedin_url": "string (URL, optional)",
           "portfolio_url": "string (URL, optional)"
       }}
    10. salary: Object. Salary expectations:
        {{
            "salary_min": "integer (positive, optional)",
            "salary_max": "integer (positive, optional)",
            "salary_currency": "string (e.g., UAH, USD, EUR, optional)"
        }}
    
    Important:
    - For date fields, use YYYY-MM format (e.g., "2023-01"). Use null for ongoing periods.
    - For boolean fields, use true/false or null if not specified.
    - For array fields, return an empty array [] if no data found.
    - For optional string fields, return null if not found.
    - Ensure the extracted dates are valid and logically consistent (start date before end date).
    - Return ONLY valid JSON.
    - Do NOT include markdown, code fences, or extra text.
    - All string values must be in English.
    
    Candidate Resume/CV Text:
    {cv_text}
    
    JSON Output:
    """
