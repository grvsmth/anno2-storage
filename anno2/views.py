"""
Views (JSON objects) for Annotator storage backend
"""

import json
from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from rest_framework import viewsets

from . import settings
from .models import Annotation
from .forms import AnnotationForm
from .serializers import UserSerializer, AnnotationSerializer

def root(request):
    return JsonResponse(settings.ANNOTATOR_API)

@csrf_exempt
def annotation(request):
    if request.method == 'POST':
        annoJson = json.loads(request.POST.get('data'))
        anno = AnnotationForm(annoJson)
        if anno.is_valid():
            anno.save()
        # return JsonResponse(list(User.objects.all()), safe=False)
            return HttpResponse(serializers.serialize("json", anno))
        else:
            return HttpResponse(json.dumps(anno.errors))
        # return HttpResponse('http://grieve-smith.com', status=303)
    elif request.method == 'GET':
        return JsonResponse(list(Annotation.objects.all()), safe=False)
    else:
        return HttpResponseBadRequest()

class AnnotationViewSet(viewsets.ModelViewSet):
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer