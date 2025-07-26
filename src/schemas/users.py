from drf_spectacular.utils import OpenApiExample, OpenApiResponse

USER_SCHEMA_EXAMPLE = {
    'id': 1,
    'username': 'john_doe',
    'email': 'john.doe@example.com',
    'first_name': 'John',
    'last_name': 'Doe',
    'avatar_url': 'https://example.com/avatar.jpg',
    'linkedin_id': 'linkedin123',
    'date_joined': '2023-01-01T00:00:00Z'
}

USER_LIST_RESPONSE = OpenApiResponse(
    response={'type': 'array', 'items': {'$ref': '#/components/schemas/User'}},
    description='Список користувачів',
    examples=[
        OpenApiExample(
            'Приклад списку користувачів',
            value=[USER_SCHEMA_EXAMPLE]
        )
    ]
)

USER_DETAIL_RESPONSE = OpenApiResponse(
    response={'$ref': '#/components/schemas/User'},
    description='Деталі користувача',
    examples=[
        OpenApiExample(
            'Приклад інформації про користувача',
            value=USER_SCHEMA_EXAMPLE
        )
    ]
)

USER_CREATE_REQUEST = {
    'type': 'object',
    'properties': {
        'username': {'type': 'string', 'example': 'john_doe'},
        'email': {'type': 'string', 'format': 'email', 'example': 'john.doe@example.com'},
        'first_name': {'type': 'string', 'example': 'John'},
        'last_name': {'type': 'string', 'example': 'Doe'},
        'avatar_url': {'type': 'string', 'format': 'uri', 'nullable': True,
                       'example': 'https://example.com/avatar.jpg'},
    },
    'required': ['username', 'email']
}

USER_CREATE_RESPONSE = OpenApiResponse(
    response={'$ref': '#/components/schemas/User'},
    description='Користувача створено',
    examples=[
        OpenApiExample(
            'Приклад створеного користувача',
            value=USER_SCHEMA_EXAMPLE
        )
    ]
)

USER_UPDATE_REQUEST = {
    'type': 'object',
    'properties': {
        'first_name': {'type': 'string', 'example': 'Jane'},
        'last_name': {'type': 'string', 'example': 'Smith'},
        'avatar_url': {'type': 'string', 'format': 'uri', 'nullable': True,
                       'example': 'https://example.com/new_avatar.jpg'},
    }
}

USER_UPDATE_RESPONSE = OpenApiResponse(
    response={'$ref': '#/components/schemas/User'},
    description='Користувача оновлено',
    examples=[
        OpenApiExample(
            'Приклад оновленого користувача',
            value={**USER_SCHEMA_EXAMPLE, 'first_name': 'Jane', 'last_name': 'Smith'}
        )
    ]
)

USER_DELETE_RESPONSE = OpenApiResponse(description='Користувача видалено')

REGISTER_REQUEST = {
    'type': 'object',
    'properties': {
        'email': {'type': 'string', 'format': 'email', 'example': 'user@example.com'},
        'username': {'type': 'string', 'example': 'newuser'},
        'password': {'type': 'string', 'example': 'securepassword123'}
    },
    'required': ['email', 'username', 'password']
}

REGISTER_RESPONSE_SUCCESS = OpenApiResponse(
    response={'type': 'object', 'properties': {'token': {'type': 'string'}}},
    description='Успішна реєстрація',
    examples=[
        OpenApiExample(
            'Приклад успішної реєстрації',
            value={'token': 'abc123def456'}
        )
    ]
)

REGISTER_RESPONSE_ERROR = OpenApiResponse(description='Помилка валідації')

LOGIN_REQUEST = {
    'type': 'object',
    'properties': {
        'email': {'type': 'string', 'format': 'email', 'example': 'user@example.com'},
        'password': {'type': 'string', 'example': 'userpassword'}
    },
    'required': ['email', 'password']
}

LOGIN_RESPONSE_SUCCESS = OpenApiResponse(
    response={'type': 'object', 'properties': {'token': {'type': 'string'}}},
    description='Успішний вхід',
    examples=[
        OpenApiExample(
            'Приклад успішного входу',
            value={'token': 'abc123def456'}
        )
    ]
)

LOGIN_RESPONSE_ERROR = OpenApiResponse(description='Помилка валідації')

CURRENT_USER_RESPONSE = OpenApiResponse(
    response={'$ref': '#/components/schemas/User'},
    description='Інформація про поточного користувача',
    examples=[
        OpenApiExample(
            'Приклад інформації про поточного користувача',
            value=USER_SCHEMA_EXAMPLE
        )
    ]
)

GOOGLE_LOGIN_REQUEST = {
    'type': 'object',
    'properties': {
        'access_token': {'type': 'string', 'example': 'ya29.a0AfH6SMC...'}
    },
    'required': ['access_token']
}

GOOGLE_LOGIN_RESPONSE_SUCCESS = OpenApiResponse(
    response={
        'type': 'object',
        'properties': {
            'token': {'type': 'string'},
            'user': {'$ref': '#/components/schemas/User'}
        }
    },
    description='Успішний вхід через Google',
    examples=[
        OpenApiExample(
            'Приклад успішного входу через Google',
            value={
                "token": "abc123def456",
                "user": USER_SCHEMA_EXAMPLE
            }
        )
    ]
)

GOOGLE_LOGIN_RESPONSE_ERROR = OpenApiResponse(
    description='Відсутній або недійсний токен Google',
    examples=[
        OpenApiExample(
            'Токен не передано',
            summary='Access token не передано',
            value={'detail': 'Access token is required.'},
            response_only=True
        ),
        OpenApiExample(
            'Недійсний токен',
            summary='Токен недійсний або прострочений',
            value={'detail': 'Google userinfo error: 401 ...'},
            response_only=True
        ),
    ]
)

LINKEDIN_LOGIN_REQUEST = {
    'type': 'object',
    'properties': {
        'access_token': {'type': 'string', 'example': 'AQXJ23V...'}
    },
    'required': ['access_token']
}

LINKEDIN_LOGIN_RESPONSE_SUCCESS = OpenApiResponse(
    response={
        'type': 'object',
        'properties': {
            'token': {'type': 'string'},
            'user': {'$ref': '#/components/schemas/User'}
        }
    },
    description='Успішний вхід через LinkedIn',
    examples=[
        OpenApiExample(
            'Приклад успішного входу через LinkedIn',
            value={
                "token": "abc123def456",
                "user": USER_SCHEMA_EXAMPLE
            }
        )
    ]
)

LINKEDIN_LOGIN_RESPONSE_ERROR = OpenApiResponse(
    description='Недійсний токен LinkedIn',
    examples=[
        OpenApiExample(
            'Недійсний токен',
            summary='Токен недійсний або неправильний',
            value={'detail': 'Invalid LinkedIn access token: ...'}
        )
    ]
)

LOGOUT_RESPONSE = OpenApiResponse(
    response={'type': 'object', 'properties': {'detail': {'type': 'string'}}},
    description='Вихід користувача (токени видалено)',
    examples=[
        OpenApiExample(
            'Успішний вихід',
            value={'detail': 'Вихід успішний'}
        )
    ]
)
