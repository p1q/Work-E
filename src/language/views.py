import io
import re
import unicodedata
import langid
import math
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser

from .serializers import LanguageDetectSerializer


class LenientJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        raw = stream.read()
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            text = raw.decode('utf-8', errors='ignore')
        cleaned = re.sub(r'[\x00-\x1F\x7F]', ' ', text)
        cleaned_stream = io.BytesIO(cleaned.encode('utf-8'))
        return super().parse(cleaned_stream, media_type, parser_context)


class LanguageDetectView(APIView):
    parser_classes = [LenientJSONParser]

    def post(self, request):
        serializer = LanguageDetectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        raw_text = serializer.validated_data['text']
        cleaned_text = unicodedata.normalize('NFC', raw_text).strip()

        lang, log_prob = langid.classify(cleaned_text)
        confidence = round(math.exp(log_prob), 4)

        return Response({
            'language': lang,
            'confidence': confidence
        })
