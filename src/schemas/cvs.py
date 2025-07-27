from drf_spectacular.utils import OpenApiExample, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

CV_SCHEMA_EXAMPLE = {
    'id': 1,
    'user': 1,
    'filename': 'my_cv.pdf',
    'uploaded_at': '2023-01-01T10:00:00Z'
}

CV_LIST_RESPONSE = OpenApiResponse(
    description='Список резюме',
    examples=[OpenApiExample('Приклад списку', value=[CV_SCHEMA_EXAMPLE])]
)

CV_DETAIL_RESPONSE = OpenApiResponse(
    description='Деталі резюме',
    examples=[OpenApiExample('Приклад резюме', value=CV_SCHEMA_EXAMPLE)]
)

CV_DELETE_RESPONSE = OpenApiResponse(description='Резюме видалено')

CV_CREATE = {
    'request': {
        'content': {
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'example': 'user@example.com'},
                    'cv_file': {'type': 'string', 'format': 'binary'}
                }
            }
        }
    },
    'responses': {
        201: OpenApiResponse(
            description='Резюме завантажено',
            examples=[OpenApiExample('Приклад створення', value=CV_SCHEMA_EXAMPLE)]
        )
    }
}

CV_BY_EMAIL = {
    'request': {
        'content': {
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'example': 'user@example.com'}
                }
            }
        }
    },
    'responses': {
        200: OpenApiResponse(
            description='Список резюме по email',
            examples=[OpenApiExample('Приклад списку', value=[CV_SCHEMA_EXAMPLE])]
        ),
        404: OpenApiResponse(description='Резюме не знайдено')
    }
}

CV_LAST_BY_EMAIL = {
    'request': CV_BY_EMAIL['request'],
    'responses': {
        200: OpenApiResponse(
            description='Останнє резюме по email',
            examples=[OpenApiExample('Приклад резюме', value=CV_SCHEMA_EXAMPLE)]
        ),
        404: OpenApiResponse(description='Резюме не знайдено')
    }
}

CV_LIST_PARAMETERS = [
    OpenApiParameter(name='email', description='Фільтр по email', required=False, type=OpenApiTypes.EMAIL)
]
