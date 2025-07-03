from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from chatgpt.service import generate_chat_response
from chatgpt.interfaces.serializers import ChatGPTRequestSerializer, ChatGPTResponseSerializer


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
                temperature=data["temperature"]
            )
        except Exception as e:
            return Response(
                {"error": f"Error when querying OpenAI: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        resp_ser = ChatGPTResponseSerializer({"response": text})
        return Response(resp_ser.data, status=status.HTTP_200_OK)
