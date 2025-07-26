from drf_spectacular.utils import OpenApiExample, OpenApiResponse

VACANCY_SCHEMA_EXAMPLE = {
    'id': 1,
    'title': 'Python Developer',
    'link': 'https://example.com/vacancy/1',
    'location': 'Київ, Україна',
    'salary': '50000-70000 грн',
    'category': 'IT',
    'date': '2023-01-01T10:00:00Z',
    'description': 'Шукаємо Python розробника...',
    'skills': 'Python, Django, REST API',
    'tools': 'Git, Docker',
    'responsibilities': 'Розробка веб-додатків...',
    'languages': 'Англійська (середній рівень)',
    'location_field': 'Київ',
    'salary_range': '50000-70000'
}

VACANCY_LIST_RESPONSE = OpenApiResponse(
    response={'type': 'array', 'items': {'$ref': '#/components/schemas/Vacancy'}},
    description='Список вакансій',
    examples=[
        OpenApiExample(
            'Приклад списку вакансій',
            value=[VACANCY_SCHEMA_EXAMPLE]
        )
    ]
)

VACANCY_DETAIL_RESPONSE = OpenApiResponse(
    response={'$ref': '#/components/schemas/Vacancy'},
    description='Деталі вакансії',
    examples=[
        OpenApiExample(
            'Приклад інформації про вакансію',
            value=VACANCY_SCHEMA_EXAMPLE
        )
    ]
)

VACANCY_CREATE_REQUEST = {
    'type': 'object',
    'properties': {
        'title': {'type': 'string', 'example': 'Python Developer'},
        'link': {'type': 'string', 'format': 'uri', 'example': 'https://example.com/vacancy/1'},
        'location': {'type': 'string', 'example': 'Київ, Україна'},
        'salary': {'type': 'string', 'nullable': True, 'example': '50000-70000 грн'},
        'category': {'type': 'string', 'example': 'IT'},
        'date': {'type': 'string', 'format': 'date-time', 'example': '2023-01-01T10:00:00Z'},
        'description': {'type': 'string', 'example': 'Шукаємо Python розробника...'},
        'skills': {'type': 'string', 'nullable': True, 'example': 'Python, Django, REST API'},
        'tools': {'type': 'string', 'nullable': True, 'example': 'Git, Docker'},
        'responsibilities': {'type': 'string', 'nullable': True, 'example': 'Розробка веб-додатків...'},
        'languages': {'type': 'string', 'nullable': True, 'example': 'Англійська (середній рівень)'},
        'location_field': {'type': 'string', 'nullable': True, 'example': 'Київ'},
        'salary_range': {'type': 'string', 'nullable': True, 'example': '50000-70000'}
    },
    'required': ['title', 'link', 'location', 'category', 'date', 'description']
}

VACANCY_CREATE_RESPONSE = OpenApiResponse(
    response={'$ref': '#/components/schemas/Vacancy'},
    description='Вакансію створено',
    examples=[
        OpenApiExample(
            'Приклад створеної вакансії',
            value=VACANCY_SCHEMA_EXAMPLE
        )
    ]
)

VACANCY_DELETE_RESPONSE = OpenApiResponse(description='Вакансію видалено')
