"""
Views (JSON objects) for Annotator storage backend
"""

from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework import viewsets

from . import settings
from .models import Annotation
from .serializers import UserSerializer, AnnotationSerializer

def root(request):
    return JsonResponse(settings.ANNOTATOR_API)

class AnnotationViewSet(viewsets.ModelViewSet):
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
