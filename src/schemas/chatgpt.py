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
            'prompt_tokens': {'type': 'integer'},
            'estimated_completion_tokens': {'type': 'integer'},
            'cost_prompt': {'type': 'number', 'format': 'float'},
            'cost_completion': {'type': 'number', 'format': 'float'},
            'total_cost': {'type': 'number', 'format': 'float'},
            'pricing': {'type': 'object'}
        }
    },
    description='Оцінка вартості запиту',
    examples=[
        OpenApiExample(
            'Приклад оцінки вартості',
            value={
                'model': 'gpt-3.5-turbo',
                'prompt_tokens': 10,
                'estimated_completion_tokens': 50,
                'cost_prompt': 0.000015,
                'cost_completion': 0.0001,
                'total_cost': 0.000115,
                'pricing': {'input': 0.0015, 'output': 0.002}
            }
        )
    ]
)
