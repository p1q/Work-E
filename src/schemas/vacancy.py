from drf_spectacular.utils import OpenApiExample, OpenApiResponse

VACANCY_SCHEMA_EXAMPLE = {
    'id': 1,
    'title': 'Senior Python Developer',
    'link': 'https://example.com/jobs/123',
    'level': 'Senior',
    'categories': ['Python', 'Backend'],
    'countries': ['UA', 'PL'],
    'cities': ['Kyiv', 'Warsaw'],
    'location': 'Kyiv',
    'is_remote': True,
    'is_hybrid': False,
    'languages': [
        {'language': 'English', 'level': 'B2'},
        {'language': 'Ukrainian', 'level': None}
    ],
    'skills': ['Python', 'Django', 'PostgreSQL', 'Docker'],
    'responsibilities': [
        'Develop and maintain web applications',
        'Collaborate with the team'
    ],
    'description': 'We are looking for an experienced Python developer...',
    'salary_min': 50000,
    'salary_max': 70000,
    'salary_currency': 'UAH'
}

VACANCY_CREATE_REQUEST = {
    'type': 'object',
    'properties': {
        'vacancy_text': {
            'type': 'string',
            'description': 'Сирий текст вакансії для обробки ШІ.',
            'example': 'We are looking for a Python developer... Experience with Django is a plus.'
        }
    },
    'required': ['vacancy_text']
}

VACANCY_CREATE_STRUCTURED_REQUEST = {
    'type': 'object',
    'properties': {
        'title': {'type': 'string', 'example': 'Senior Python Developer'},
        'link': {'type': 'string', 'nullable': True, 'example': 'https://example.com/jobs/123'},
        'level': {'type': 'string', 'nullable': True, 'example': 'Senior'},
        'categories': {
            'type': 'array',
            'items': {'type': 'string'},
            'example': ['Python', 'Backend']
        },
        'countries': {
            'type': 'array',
            'nullable': True,
            'items': {'type': 'string'},
            'example': ['UA', 'PL']
        },
        'cities': {
            'type': 'array',
            'nullable': True,
            'items': {'type': 'string'},
            'example': ['Kyiv', 'Warsaw']
        },
        'location': {'type': 'string', 'nullable': True, 'example': 'Kyiv'},
        'is_remote': {'type': 'boolean', 'nullable': True, 'example': True},
        'is_hybrid': {'type': 'boolean', 'nullable': True, 'example': False},
        'languages': {
            'type': 'array',
            'nullable': True,
            'items': {
                'type': 'object',
                'properties': {
                    'language': {'type': 'string', 'example': 'English'},
                    'level': {'type': 'string', 'nullable': True, 'example': 'B2'}
                },
                'required': ['language']
            },
            'example': [{'language': 'English', 'level': 'B2'}, {'language': 'Ukrainian'}]
        },
        'skills': {
            'type': 'array',
            'items': {'type': 'string'},
            'example': ['Python', 'Django', 'PostgreSQL']
        },
        'responsibilities': {
            'type': 'array',
            'items': {'type': 'string'},
            'example': ['Develop web applications', 'Write unit tests']
        },
        'description': {'type': 'string', 'nullable': True, 'example': 'We are looking for a Python developer...'},
        'salary_min': {'type': 'integer', 'nullable': True, 'example': 50000},
        'salary_max': {'type': 'integer', 'nullable': True, 'example': 70000},
        'salary_currency': {'type': 'string', 'nullable': True, 'example': 'UAH'},
    },
    'required': ['title', 'categories']
}

# Відповіді API
VACANCY_LIST_RESPONSE = OpenApiResponse(
    description='Список вакансій',
    examples=[OpenApiExample('Приклад списку', value=[VACANCY_SCHEMA_EXAMPLE])]
)

VACANCY_DETAIL_RESPONSE = OpenApiResponse(
    description='Деталі вакансії',
    examples=[OpenApiExample('Приклад вакансії', value=VACANCY_SCHEMA_EXAMPLE)]
)

VACANCY_CREATE_RESPONSE = OpenApiResponse(
    response={'$ref': '#/components/schemas/Vacancy'},
    description='Вакансію створено',
    examples=[OpenApiExample('Приклад створеної вакансії', value=VACANCY_SCHEMA_EXAMPLE)]
)

VACANCY_DELETE_RESPONSE = OpenApiResponse(
    description='Вакансію видалено'
)
