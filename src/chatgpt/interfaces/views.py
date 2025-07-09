from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema

from chatgpt.service import generate_chat_response, estimate_cost
from chatgpt.interfaces.serializers import (
    ChatGPTRequestSerializer,
    ChatGPTResponseSerializer,
    ChatGPTPlanRequestSerializer,
    ChatGPTPlanResponseSerializer,
)


@extend_schema(exclude=True)
class ChatGPTAPIView(APIView):
    permission_classes = [AllowAny]

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
                {"error": f"Error when querying OpenAI: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        resp_ser = ChatGPTResponseSerializer({"response": text})
        return Response(resp_ser.data, status=status.HTTP_200_OK)


@extend_schema(exclude=True)
class ChatGPTPlanAPIView(APIView):
    permission_classes = [AllowAny]

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
