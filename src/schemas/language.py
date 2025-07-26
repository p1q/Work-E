from drf_spectacular.utils import OpenApiExample, OpenApiResponse

LANGUAGE_DETECT_REQUEST = {
    'type': 'object',
    'properties': {
        'text': {'type': 'string', 'example': 'Hello, world!'}
    },
    'required': ['text']
}

LANGUAGE_DETECT_RESPONSE = OpenApiResponse(
    response={'type': 'object',
              'properties': {'language': {'type': 'string'}, 'confidence': {'type': 'number', 'format': 'float'}}},
    description='Визначення мови',
    examples=[
        OpenApiExample(
            'Приклад визначення мови',
            value={'language': 'en', 'confidence': 0.9876}
        )
    ]
)
