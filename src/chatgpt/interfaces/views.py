from chatgpt.interfaces.serializers import (ChatGPTRequestSerializer, ChatGPTResponseSerializer,
                                            ChatGPTPlanRequestSerializer, ChatGPTPlanResponseSerializer, )
from chatgpt.service import generate_chat_response, estimate_cost
from drf_spectacular.utils import extend_schema, OpenApiRequest, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from src.schemas.chatgpt import (CHATGPT_REQUEST, CHATGPT_RESPONSE, CHATGPT_PLAN_REQUEST, CHATGPT_PLAN_RESPONSE, )

CHATGPT_VIEW_RESPONSE_ERROR = OpenApiResponse(
    response={'type': 'object', 'properties': {'error': {'type': 'string'}}},
    description='Помилка сервера',
    examples=[
        OpenApiResponse.example(
            name='Помилка при запиті до OpenAI',
            value={'error': 'Помилка при запиті до OpenAI: ...'}
        )
    ]
)


class ChatGPTAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=OpenApiRequest(CHATGPT_REQUEST),
        responses={
            200: CHATGPT_RESPONSE,
            500: CHATGPT_VIEW_RESPONSE_ERROR,
        },
        description='Надсилає запит до моделі OpenAI та повертає відповідь.',
        summary='Отримати відповідь від ChatGPT'
    )
    def post(self, request):
        req_ser = ChatGPTRequestSerializer(data=request.data)
        req_ser.is_valid(raise_exception=True)
        data = req_ser.validated_data
        try:
            text = generate_chat_response(
                prompt=data["prompt"],
                model=data["model"],
                temperature=data["temperature"],
            )
        except Exception as e:
            return Response(
                {"error": f"Помилка при запиті до OpenAI: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        resp_ser = ChatGPTResponseSerializer({"response": text})
        return Response(resp_ser.data, status=status.HTTP_200_OK)


class ChatGPTPlanAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=OpenApiRequest(CHATGPT_PLAN_REQUEST),
        responses={
            200: CHATGPT_PLAN_RESPONSE,
        },
        description='Оцінює вартість запиту до моделі OpenAI на основі кількості токенів.',
        summary='Оцінити вартість запиту до ChatGPT'
    )
    def post(self, request):
        req_ser = ChatGPTPlanRequestSerializer(data=request.data)
        req_ser.is_valid(raise_exception=True)
        data = req_ser.validated_data
        info = estimate_cost(
            prompt=data["prompt"],
            model=data["model"],
            max_tokens=data["max_tokens"],
        )
        resp_ser = ChatGPTPlanResponseSerializer(info)
        return Response(resp_ser.data, status=status.HTTP_200_OK)
