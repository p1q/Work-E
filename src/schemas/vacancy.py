from drf_spectacular.utils import OpenApiExample, OpenApiResponse

VACANCY_SCHEMA_EXAMPLE = {
    'id': 1,
    'title': 'Python Developer',
    'link': 'https://example.com/vacancy/1',
    'countries': ['UA'],
    'cities': ['Kyiv', 'Remote'],
    'salary_min': 50000,
    'salary_max': 70000,
    'salary_currency': 'UAH',
    'categories': ['Python', 'DevOps'],
    'date': '2023-01-01T10:00:00Z',
    'description': 'Шукаємо Python розробника...',
    'skills': 'Python, Django, REST API',
    'tools': 'Git, Docker',
    'responsibilities': 'Розробка веб-додатків...',
    'languages': 'Англійська (середній рівень)',
    'location': 'Україна, Київ, Віддалено',
    'salary_range': '50000-70000 UAH'
}

VACANCY_LIST_RESPONSE = OpenApiResponse(
    response={'type': 'array', 'items': {'type': 'object', 'properties': VACANCY_SCHEMA_EXAMPLE}},
    description='Список вакансій',
    examples=[
        OpenApiExample(
            'Приклад списку вакансій',
            value=[VACANCY_SCHEMA_EXAMPLE]
        )
    ]
)

VACANCY_DETAIL_RESPONSE = OpenApiResponse(
    response={'type': 'object', 'properties': VACANCY_SCHEMA_EXAMPLE},
    description='Деталі вакансії',
    examples=[
        OpenApiExample(
            'Приклад інформації про вакансію',
            value=VACANCY_SCHEMA_EXAMPLE
        )
    ]
)

VACANCY_CREATE_REQUEST = {
    'request': {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'title': {'type': 'string', 'example': 'Python Developer'},
                        'link': {'type': 'string', 'format': 'uri', 'nullable': True,
                                 'example': 'https://example.com/vacancy/1'},
                        'countries': {'type': 'array', 'items': {'type': 'string'}, 'example': ['UA']},
                        'cities': {'type': 'array', 'items': {'type': 'string'}, 'example': ['Kyiv', 'Remote']},
                        'salary_min': {'type': 'integer', 'nullable': True, 'example': 50000},
                        'salary_max': {'type': 'integer', 'nullable': True, 'example': 70000},
                        'salary_currency': {'type': 'string', 'nullable': True, 'example': 'UAH'},
                        'categories': {'type': 'array', 'items': {'type': 'string'}, 'example': ['Python', 'DevOps']},
                        'description': {'type': 'string', 'example': 'Шукаємо Python розробника...'},
                        'skills': {'type': 'string', 'nullable': True, 'example': 'Python, Django, REST API'},
                        'tools': {'type': 'string', 'nullable': True, 'example': 'Git, Docker'},
                        'responsibilities': {'type': 'string', 'nullable': True, 'example': 'Розробка веб-додатків...'},
                        'languages': {'type': 'string', 'nullable': True, 'example': 'Англійська (середній рівень)'},
                    },
                    'required': ['title', 'categories', 'description']
                }
            }
        }
    },
    'responses': {
        201: OpenApiResponse(
            response={'type': 'object', 'properties': VACANCY_SCHEMA_EXAMPLE},
            description='Вакансію створено',
            examples=[
                OpenApiExample(
                    'Приклад створеної вакансії',
                    value=VACANCY_SCHEMA_EXAMPLE
                )
            ]
        )
    }
}

VACANCY_DELETE_RESPONSE = OpenApiResponse(description='Вакансію видалено')
