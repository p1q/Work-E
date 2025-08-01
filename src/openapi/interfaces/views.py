import logging

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OpenAPIChatRequestSerializer, OpenAPIChatResponseSerializer
from ..service import call_openapi_ai

logger = logging.getLogger(__name__)

class OpenAPIChatView(APIView):
    permission_classes = [AllowAny] #[IsAuthenticated] для ограничения доступа

    @extend_schema(
        summary="Відправити повідомлення в OpenAPI ШІ",
        description="Відправляє повідомлення в зазначений OpenAPI-совмістимий ШІ та повертає його відповідь.",
        request=OpenAPIChatRequestSerializer,
        responses={
            200: OpenApiResponse(response=OpenAPIChatResponseSerializer, description='Успішна відповідь ШІ'),
            400: OpenApiResponse(description='Помилка валідації запиту'),
            500: OpenApiResponse(description='Помилка виклику ШІ або обробки відповіді'),
        },
        examples=[
            OpenApiExample(
                'Приклад запиту',
                summary='Просте привітання',
                value={
                    "messages": [{"role": "user", "content": "привіт"}],
                    "model": "qwen-max-latest",
                    "chatId": ""
                }
            ),
            OpenApiExample(
                'Приклад відповіді',
                summary='Відповідь ШІ',
                value={
                    "ai_response": {
                        "message": {"content": "Привіт! Як я можу вам допомогти?"}
                    }
                },
                response_only=True,
            ),
        ]
    )
    def post(self, request):
        serializer = OpenAPIChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Невірні дані отримано для OpenAPI чату: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        messages = validated_data.get('messages')
        model = validated_data.get('model')
        chat_id = validated_data.get('chatId', '')

        logger.info(f"Викликаємо OpenAPI ШІ з повідомленнями: {messages[:100]}...")
        try:
            ai_response_data = call_openapi_ai(messages=messages, model=model, chat_id=chat_id)

            if not ai_response_data:
                logger.error("OpenAPI ШІ сервіс повернув порожню відповідь.")
                return Response({"error": "Не вдалося отримати відповідь від ШІ"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            response_data = {"ai_response": ai_response_data}
            response_serializer = OpenAPIChatResponseSerializer(data=response_data)

            logger.info("Відповідь OpenAPI ШІ успішно відправлена.")
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Несподівана помилка під час виклику OpenAPI ШІ.")
            return Response({"error": f"Сталася несподівана помилка: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
