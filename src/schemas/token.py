from drf_spectacular.utils import OpenApiExample, OpenApiResponse

TOKEN_OBTAIN_REQUEST = {
    "type": "object",
    "properties": {
        "email": {"type": "string", "example": "user@example.com"},
        "password": {"type": "string", "example": "userpassword"},
    },
    "required": ["email", "password"],
}

TOKEN_OBTAIN_RESPONSE = {
    "type": "object",
    "properties": {
        "access": {"type": "string"},
        "refresh": {"type": "string"},
    },
    "example": {
        "access": "eyJ0eXAiOiJKV1QiLCJh...",
        "refresh": "eyJhbGciOiJIUzI1NiIsInR...",
    },
}

TOKEN_OBTAIN_RESPONSE_UNAUTHORIZED = OpenApiExample(
    name="Unauthorized",
    value={"detail": "No active account found with the given credentials"},
)

TOKEN_REFRESH_REQUEST = {
    "type": "object",
    "properties": {
        "refresh": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR..."}
    },
    "required": ["refresh"],
}

TOKEN_REFRESH_RESPONSE = {
    "type": "object",
    "properties": {
        "access": {"type": "string"},
        "refresh": {"type": "string"},
    },
    "example": {
        "access": "eyJ0eXAiOiJKV1QiLCJh...",
        "refresh": "eyJhbGciOiJIUzI1NiIsInR...",
    },
}

TOKEN_REFRESH_RESPONSE_INVALID = OpenApiExample(
    name="Invalid token",
    value={"detail": "Token is invalid or expired"},
)
