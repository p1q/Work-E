import io
import math
import re

import langid
import unicodedata
from drf_spectacular.utils import extend_schema, OpenApiRequest
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from src.language.interfaces.serializers import LanguageDetectSerializer, LanguageDetectResponseSerializer
from src.schemas.language import LANGUAGE_DETECT_RESPONSE, LANGUAGE_DETECT_REQUEST


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
    permission_classes = [AllowAny]
    parser_classes = [LenientJSONParser]

    @extend_schema(
        request=OpenApiRequest(LANGUAGE_DETECT_REQUEST),
        responses={
            200: LANGUAGE_DETECT_RESPONSE,
        },
        description='Визначає мову тексту за допомогою бібліотеки langid.',
        summary='Визначити мову тексту'
    )
    def post(self, request):
        serializer = LanguageDetectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_text = serializer.validated_data['text']
        cleaned_text = unicodedata.normalize('NFC', raw_text).strip()
        lang, log_prob = langid.classify(cleaned_text)
        confidence = round(math.exp(log_prob), 4)
        resp_ser = LanguageDetectResponseSerializer({
            'language': lang,
            'confidence': confidence
        })
        return Response(resp_ser.data)
