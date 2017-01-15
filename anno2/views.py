"""
Views (JSON objects) for Annotator storage backend
"""

import logging
from collections import OrderedDict
import django_filters.rest_framework
from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from . import settings
from .models import Annotation
from .serializers import UserSerializer, AnnotationSerializer

LOG = logging.getLogger(__name__)

def root(request):
    return JsonResponse(settings.ANNOTATOR_API)

class LimitOffsetTotalRowsPagination(LimitOffsetPagination):
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('total', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('rows', data)
        ]))

class SearchViewSet(viewsets.ModelViewSet):
    serializer_class = AnnotationSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    pagination_class = LimitOffsetTotalRowsPagination
    def get_queryset(self):
        queryset = Annotation.objects.all()
        # TODO repeat for all possible queries?
        # TODO definitely url
        text = self.request.query_params.get('text', None)
        if text is not None:
            queryset = queryset.filter(text=text)
        quote = self.request.query_params.get('quote', None)
        if quote is not None:
            queryset = queryset.filter(quote=quote)
        return queryset

class AnnotationViewSet(viewsets.ModelViewSet):
    serializer_class = AnnotationSerializer
    queryset = Annotation.objects.all()

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

