from drf_spectacular.utils import OpenApiExample, OpenApiResponse

CHATGPT_REQUEST = {
    'type': 'object',
    'properties': {
        'prompt': {'type': 'string', 'example': 'Напиши короткий вірш про Python.'},
        'model': {'type': 'string', 'example': 'gpt-3.5-turbo'},
        'temperature': {'type': 'number', 'format': 'float', 'example': 0.7}
    },
    'required': ['prompt']
}

CHATGPT_RESPONSE = OpenApiResponse(
    response={'type': 'object', 'properties': {'response': {'type': 'string'}}},
    description='Відповідь моделі',
    examples=[
        OpenApiExample(
            'Приклад відповіді',
            value={'response': 'Python — чудова мова програмування!'}
        )
    ]
)

CHATGPT_PLAN_REQUEST = {
    'type': 'object',
    'properties': {
        'prompt': {'type': 'string', 'example': 'Напиши короткий вірш про Python.'},
        'model': {'type': 'string', 'example': 'gpt-3.5-turbo'},
        'max_tokens': {'type': 'integer', 'example': 100}
    },
    'required': ['prompt']
}

CHATGPT_PLAN_RESPONSE = OpenApiResponse(
    response={
        'type': 'object',
        'properties': {
            'model': {'type': 'string'},
            'input_tokens': {'type': 'integer'},
            'output_tokens': {'type': 'integer'},
            'total_cost': {'type': 'number', 'format': 'float'}
        }
    },
    description='Оцінка вартості',
    examples=[
        OpenApiExample(
            'Приклад оцінки',
            value={
                'model': 'gpt-3.5-turbo',
                'input_tokens': 10,
                'output_tokens': 20,
                'total_cost': 0.000325
            }
        )
    ]
)

CHATGPT_VIEW_RESPONSE_ERROR = OpenApiResponse(
    response={'type': 'object', 'properties': {'error': {'type': 'string'}}},
    description='Помилка сервера',
    examples=[
        OpenApiExample(
            name='Помилка при запиті до OpenAI',
            value={'error': 'Помилка при запиті до OpenAI: ...'}
        )
    ]
)
