"""
Views (JSON objects) for Annotator storage backend
"""

import django_filters.rest_framework
from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework import viewsets

from . import settings
from .models import Annotation
from .serializers import UserSerializer, AnnotationSerializer

def root(request):
    return JsonResponse(settings.ANNOTATOR_API)

class AnnotationViewSet(viewsets.ModelViewSet):
    serializer_class = AnnotationSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)

    def get_queryset(self):
        # TODO separate view that returns total and rows fields
        queryset = Annotation.objects.all()
        # TODO repeat for all possible queries?
        text = self.request.query_params.get('text', None)
        if text is not None:
            queryset = queryset.filter(text=text)
        return queryset

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

