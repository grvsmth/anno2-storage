"""
Views (JSON objects) for Annotator storage backend
"""

import datetime
import jwt
import logging
import os
import re
from collections import OrderedDict
from urllib.parse import urlparse

import django_filters.rest_framework
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template import loader
from rest_framework import status
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
import requests
from bs4 import BeautifulSoup

from .models import Annotation
from .serializers import UserSerializer, AnnotationSerializer

LOG = logging.getLogger(__name__)

CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')
CONSUMER_TTL = 86400

ACCEPTABLE_URLS = [
    re.compile(r'^https://(www.)?panix.com/~grvsmth/stage/'),
    re.compile(r'^https://grvsmth.pythonanywhere.com/static/')
    ]

def generate_token(user_id):
    """
    Generate JWT (Javascript Web Token)
    """
    return jwt.encode({
      'consumerKey': CONSUMER_KEY,
      'userId': user_id,
      'issuedAt': _now().isoformat() + 'Z',
      'ttl': CONSUMER_TTL
    }, CONSUMER_SECRET)

def _now():
    return datetime.datetime.utcnow().replace(microsecond=0)

@login_required
def profile(request):
    """
    Present annotations to user, with possibility of saving
    """
    uris = Annotation.objects.values('uri').distinct()
    t = loader.get_template('profile.html')
    return HttpResponse(t.render({'uris': uris}))

@login_required
def save_anno(request):
    """
    Save annotations to file in 'output' directory
    """
    uri = request.GET['uri']
    uripath = urlparse(uri).path
    basename = os.path.basename(uripath)
    filename = os.path.splitext(basename)[0] + '.json'
    filepath = os.path.join(settings.BASE_DIR, 'output', filename)
    annos = Annotation.objects.filter(uri=uri)
    annoJson = JSONRenderer().render(AnnotationSerializer(list(annos), many=True).data)
    annoDictJson = '{"' + uri + '": ' + annoJson.decode("utf-8") + '}'
    with open(filepath, 'w') as outfile:
        outfile.write(annoDictJson)
    return HttpResponse('', status=status.HTTP_201_CREATED)

@login_required
def root(request):
    return JsonResponse(settings.ANNOTATOR_API)

@login_required
def token(request):
    return(HttpResponse(generate_token(request.user.username)))

def repanix(request):
    pageUrl = request.GET.get('url')
    LOG.error(pageUrl)
    urlOk = False
    for urlRe in ACCEPTABLE_URLS:
        urlMatch = urlRe.match(pageUrl)
        if urlMatch:
            urlOk = True

    t = loader.get_template('stage.html')
    if urlOk:
        res = requests.get(pageUrl)
        body = ""
        if res.status_code != 200:
            body = "Error retrieving web page {}: {}".format(pageUrl, res.status_code)
            LOG.error(body)

        soup = BeautifulSoup(res.content, 'html.parser')
        content = soup.select('.Content')
        if not content:
            content = soup.select('.play')
        body = str(content[0])
    else:
        body = "The url <strong>{}</strong> does not match the list of acceptable URLs".format(pageUrl)
        LOG.error(body)

    trender = t.render(
        {
            'body': body,
            'url': pageUrl,
            'serverUri': os.environ.get('DJANGO_HOST')
            }
            )
    return HttpResponse(trender)

def jsfile(request):
    """
    Return the anno2.js file with the URL of this server
    """
    # LOG.error("jsfile: %s", os.environ.get('DJANGO_HOST'))
    return render(request, 'anno2.js', {'url': os.environ.get('DJANGO_HOST')})

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
        text = self.request.query_params.get('text', None)
        if text is not None:
            queryset = queryset.filter(text=text)
        quote = self.request.query_params.get('quote', None)
        if quote is not None:
            queryset = queryset.filter(quote=quote)
        uri = self.request.query_params.get('uri', None)
        if uri is not None:
            queryset = queryset.filter(uri=uri)
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

