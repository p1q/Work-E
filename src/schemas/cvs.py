from drf_spectacular.utils import OpenApiExample, OpenApiResponse

CV_SCHEMA_EXAMPLE = {
    'id': 1,
    'user': 1,
    'filename': 'my_cv.pdf',
    'uploaded_at': '2023-01-01T10:00:00Z'
}

CV_LIST_RESPONSE = OpenApiResponse(
    response={'type': 'array', 'items': {'$ref': '#/components/schemas/CV'}},
    description='Список резюме',
    examples=[
        OpenApiExample(
            'Приклад списку резюме',
            value=[CV_SCHEMA_EXAMPLE]
        )
    ]
)

CV_DETAIL_RESPONSE = OpenApiResponse(
    response={'$ref': '#/components/schemas/CV'},
    description='Деталі резюме',
    examples=[
        OpenApiExample(
            'Приклад інформації про резюме',
            value=CV_SCHEMA_EXAMPLE
        )
    ]
)

CV_CREATE_REQUEST = {
    'type': 'object',
    'properties': {
        'email': {'type': 'string', 'format': 'email', 'example': 'user@example.com'},
        'cv_file': {'type': 'string', 'format': 'binary'}
    },
    'required': ['email', 'cv_file']
}

CV_CREATE_RESPONSE = OpenApiResponse(
    response={'$ref': '#/components/schemas/CV'},
    description='Резюме завантажено',
    examples=[
        OpenApiExample(
            'Приклад створеного резюме',
            value=CV_SCHEMA_EXAMPLE
        )
    ]
)

CV_DELETE_RESPONSE = OpenApiResponse(description='Резюме видалено')

CV_BY_EMAIL_REQUEST = {
    'type': 'object',
    'properties': {
        'email': {'type': 'string', 'format': 'email', 'example': 'user@example.com'}
    },
    'required': ['email']
}

CV_BY_EMAIL_RESPONSE_SUCCESS = OpenApiResponse(
    response={'type': 'array', 'items': {'$ref': '#/components/schemas/CV'}},
    description='Список резюме для вказаної електронної пошти',
    examples=[
        OpenApiExample(
            'Приклад списку резюме',
            value=[CV_SCHEMA_EXAMPLE]
        )
    ]
)

CV_BY_EMAIL_RESPONSE_NOT_FOUND = OpenApiResponse(
    description='Резюме для вказаної електронної пошти не знайдено',
    examples=[
        OpenApiExample(
            'Резюме не знайдено',
            value={'detail': 'No CVs found for email "user@example.com".'}
        )
    ]
)

CV_LAST_BY_EMAIL_RESPONSE_SUCCESS = OpenApiResponse(
    response={'$ref': '#/components/schemas/CV'},
    description='Останнє резюме для вказаної електронної пошти',
    examples=[
        OpenApiExample(
            'Приклад останнього резюме',
            value=CV_SCHEMA_EXAMPLE
        )
    ]
)

CV_LAST_BY_EMAIL_RESPONSE_NOT_FOUND = OpenApiResponse(
    description='Резюме для вказаної електронної пошти не знайдено',
    examples=[
        OpenApiExample(
            'Резюме не знайдено',
            value={'detail': 'No CV found for email "user@example.com".'}
        )
    ]
)
