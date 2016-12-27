"""
Views (JSON objects) for Annotator storage backend
"""

import json
from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from . import settings
from .models import Annotation
from .forms import AnnotationForm

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