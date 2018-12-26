"""
Views (JSON objects) for Annotator storage backend
"""

from copy import deepcopy
import datetime
import jwt
import logging
import os
import re
from collections import OrderedDict
from math import sqrt
from urllib.parse import urlparse

import django_filters.rest_framework
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.template import loader
from django.template.defaulttags import register
from rest_framework import status
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

import requests
from bs4 import BeautifulSoup, Tag
from numpy import mean, var
from scipy.stats import ttest_1samp

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

CONTENT_CLASSES = ['Content', 'content', 'play']

PUNCRE = re.compile('([.;?!]+)')
RANGERE = re.compile('/(\w+)\[(\d+)\]')
DIVRANGERE = re.compile('/div\[(\d+)\]/p\[(\d+)\]')
PCLASSRE = re.compile('(\w+?)(\d+)')

INTERJECTIONS = [
    'ah', 'ciel', 'oh', 'eh', 'eh, eh', 'quoi', 'toi', 'oui', 'non', 'oye',
    'oye, oye',
    'oye-', 'o ciel', 'crac', 'mon dieu', 'o mon dieu', "v'lan"
    ]

CORPORA = ['frantext', 'dps']
POSITIONS = ['ld', 'rd']
FRANTEXT = ['2021MorH4b', '2330pinto2d', 'coelina-e3b', 'wallstein1a']
EXCLUDE_TEXTS = ['1563Jocrisse3a']
TALLY_TAGS = ['ci', 'clld', 'conjoined', 'ct', 'dem', 'meme', 'pour', 'quant']
NOT_CLLD_TAGS = set(['ci', 'ct', 'conjoined', 'meme'])


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
    # return key


@register.filter
def percent(number):
    return '{:.5%}'.format(number)


@register.filter
def places_5(number):
    return '{0:.5f}'.format(number)


def cohend(d1, d2):
    # https://machinelearningmastery.com/effect-size-measures-in-python/
	# calculate the size of samples
	n1, n2 = len(d1), len(d2)
	# calculate the variance of the samples
	s1, s2 = var(d1, ddof=1), var(d2, ddof=1)
	# calculate the pooled standard deviation
	s = sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
	# calculate the means of the samples
	u1, u2 = mean(d1), mean(d2)
	# calculate the effect size
	return (u1 - u2) / s


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
    pages = {}
    for uri in uris:
        name = text_name(uri['uri'])
        pages[name] = uri['uri']
    return HttpResponse(t.render({'uris': uris, 'pages': sorted(pages.items())}))

def text_name(uri):
    """
    Given a text URI, return the base name of the text
    """
    uripath = urlparse(uri).path
    basename = os.path.basename(uripath)
    return os.path.splitext(basename)[0]

@login_required
def save_anno(request):
    """
    Save annotations to file in 'output' directory
    """
    uri = request.POST.get('uri')
    if not uri:
        return HttpResponse('')
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

def get_body_and_content_class(uri):
    """
    Extract the body and content code from the text
    """
    res = requests.get(uri)
    body = ""
    content = []
    content_class = ""
    soup = None

    if res.status_code != 200:
        body = "Error retrieving web page {}: {}".format(uri, res.status_code)
        LOG.error(body)
    else:
        soup = BeautifulSoup(res.content, 'html.parser')

        for cclass in CONTENT_CLASSES:
            content = soup.select('.' + cclass)
            if content:
                content_class = '.' + cclass
                break

        if content:
            body = str(content[0])
        else:
            body = "No content class ('.Content', '.content' or 'body') found in page!"
            LOG.error(body)

    return (body, soup, content_class)


@login_required
def repanix(request):
    pageUrl = request.GET.get('uri')
    LOG.error("repanix(%s)", pageUrl)
    urlOk = False
    content_class = '.Content'
    title = ''

    for urlRe in ACCEPTABLE_URLS:
        urlMatch = urlRe.match(pageUrl)
        if urlMatch:
            urlOk = True

    t = loader.get_template('stage.html')
    if urlOk:
        (body, soup, content_class) = get_body_and_content_class(pageUrl)
        if soup.title:
            title = soup.title.string
        else:
            title = pageUrl.split('/')[-1]
    else:
        body = "The url <strong>{}</strong> does not match the list of acceptable URLs".format(pageUrl)
        LOG.error(body)

    trender = t.render(
        {
            'body': body,
            'url': pageUrl,
            'title': title,
            'content_class': content_class,
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


@login_required
def reports(request):
    """
    Show the reports homepage
    """
    pages = {}
    uris = Annotation.objects.values('uri').distinct()
    for uri in uris:
        name = text_name(uri['uri'])
        pages[name] = uri['uri']
    return render(
        request, 'reports.html', {'uris': uris, 'pages': pages.items()}
        )


def get_position(tags):
    """
    Given a list of tags, determine if the annotation contains 'ld', 'rd' or
    neither
    """
    position = None
    for tag in tags:
        if tag.name == 'ld':
            position = 'ld'
            break
        if tag.name == 'rd':
            position = 'rd'
            break
    return position


def is_clld(tags):
    """
    Given a list of tags, determine if this is an example of clitic left
    dislocation
    """
    anno_is_clld = True
    anno_tags = set(tags)
    intersection = NOT_CLLD_TAGS & anno_tags
    if len(intersection):
        anno_is_clld = False

    return anno_is_clld


def dislocation_data(uri):
    """
    Generate per-text data for dislocation report
    """
    annos = Annotation.objects.filter(uri=uri)
    (_, soup, cclass) = get_body_and_content_class(uri)
    classes = set()
    char = {}
    totalsent = 0
    totalq = 0
    position_count = {'ld': {'clld': 0}, 'rd': {'clld': 0}}

    paras = soup.select(cclass)[0].find_all('p')
    for idx, para in enumerate(paras):
        if not para.get('class'):
            continue
        classes.update(para['class'])
        pclass = para['class'][0]
        cmatch = PCLASSRE.match(pclass)
        if not cmatch:
            continue

        cname = cmatch.group(1)
        cid = int(cmatch.group(2))
        char.setdefault(
            cid,
            {
                'name': None,
                'tcount': {'clld': 0},
                'tlcount': {},
                'paras': 0,
                'sents': 0,
                'questions': 0,
                'position_count': deepcopy(position_count)
                }
            )
        if cname == 'charn':
            if char[cid]['name']:
                continue
            charname = next(para.stripped_strings)
            char[cid]['name'] = charname
            if ',' in charname:
                char[cid]['name'] = charname.split(',')[0]
            continue

        char[cid]['paras'] += 1
        text = ''
        for pcontent in para.children:
            if isinstance(pcontent, Tag):
                if pcontent.name != 'span':
                    text += pcontent.text
            else:
                text += pcontent

        # remove non-breaking spaces
        text = text.replace('\xa0',' ')
        sentences = PUNCRE.split(text)
        for idx, sent in enumerate(sentences):
            if idx % 2 != 0:
                if '?' in sent:
                    char[cid]['questions'] += 1
                    totalq += 1
                continue

            sent = sent.strip()
            if len(sent) > 0 and sent.lower() not in INTERJECTIONS:
                char[cid]['sents'] += 1
                totalsent += 1

    divs = soup.select(cclass)[0].find_all('div')
    pcount = 0
    pnum = {}
    for didx, div in enumerate(divs):
        pnum[didx] = {}
        for idx, para in enumerate(div.find_all('p')):
            pnum[didx][idx] = pcount
            pcount += 1

    annod = {}
    tcount = {'clld': 0}
    tlcount = {}
    for anno in annos:
        startd = 0
        startp = 0
        rtype = ''

        position = get_position(anno.tags.all())
        if not position:
            continue

        arange = anno.ranges.all()[:1][0]
        rmatch = DIVRANGERE.match(arange.start)
        if rmatch:
            rtype = 'p'
            startd = int(rmatch.group(1))-1
            startp = int(rmatch.group(2))-1
            para = paras[pnum[startd][startp]]
        else:
            rmatch = RANGERE.match(arange.start)
            if rmatch:
                rtype = rmatch.group(1)
                startp = int(rmatch.group(2))-1
            if rtype != 'p':
                continue

            if len(paras) <startp:
                continue
            para = paras[startp]

        if not para.get('class'):
            annod[anno.id] = {'error': 'no class'}
            continue

        cmatch = PCLASSRE.match(para['class'][0])
        if not cmatch:
            continue
        cid = int(cmatch.group(2))
        cname = char[cid]['name']

        tags = []
        for tag in anno.tags.all():
            if tag.name != position:
                position_count[position].setdefault(tag.name, 0)
                position_count[position][tag.name] += 1
                char[cid]['position_count'][position].setdefault(tag.name, 0)
                char[cid]['position_count'][position][tag.name] += 1

            tags.append(tag.name)
            tcount.setdefault(tag.name, 0)
            tcount[tag.name] += 1
            char[cid]['tcount'].setdefault(tag.name, 0)
            char[cid]['tcount'][tag.name] += 1

        if is_clld(tags):
            tags.append('clld')
            tcount['clld'] += 1
            char[cid]['tcount']['clld'] += 1
            position_count[position]['clld'] += 1
            char[cid]['position_count'][position]['clld'] += 1

        tlist = ' '.join(sorted(tags))
        tlcount.setdefault(tlist, 0)
        tlcount[tlist] += 1

        char[cid]['tlcount'].setdefault(tlist, 0)
        char[cid]['tlcount'][tlist] += 1

        annod[anno.id] = {
            'startp': startp,
            'tags': tlist,
            'quote': anno.quote,
            'para': para,
            'char': cid
            }

    for tlist in tcount.keys():
        for cid in char:
            char[cid].setdefault(tlist, 0)

    LOG.error("%s: tcount['clld'] = %s", text_name(uri), tcount['clld'])
    data = {
        'uri': uri,
        'text_name': text_name(uri),
        'annos': annos,
        'cclass': cclass,
        'numpara': len(paras),
        'sentences': totalsent,
        'questions': totalq,
        'char': sorted(char.items()),
        'tcount': sorted(tcount.items()),
        'tcountu': tcount,
        'tlcount': sorted(tlcount.items()),
        'tlcountu': tlcount,
        'position_count': position_count,
        'annod': sorted(annod.items()),
        'debug': None
        }

    return data


@login_required
def dislocations(request):
    """
    Generate dislocation reports
    """
    uri=request.GET.get('uri')
    data = dislocation_data(uri)
    return render(request, 'dislocations.html', data)


@login_required
def all_dislocations(request):
    texts = []
    tag_count = {'dps': {}, 'frantext': {}}
    tag_percent = {'dps': {}, 'frantext': {}}
    tag_avg_percent = {'dps': {}, 'frantext': {}}
    tag_total_count = {'dps': {}, 'frantext': {}}
    text_count = {'dps': 0, 'frantext': 0}
    sentence_count = {'dps': 0, 'frantext': 0}
    question_count = {'dps': 0, 'frantext': 0}
    tag_ttest = {}
    tag_es = {}

    uris = Annotation.objects.values('uri').distinct()
    for uri in uris:
        name = text_name(uri['uri'])
        if name in EXCLUDE_TEXTS:
            continue

        text_data = dislocation_data(uri['uri'])
        texts.append(text_data)

        sentences = text_data['sentences']

        corpus = 'dps'
        if name in FRANTEXT:
            corpus = 'frantext'

        text_count[corpus] += 1
        sentence_count[corpus] += sentences
        question_count[corpus] += text_data['questions']

        for position in POSITIONS:
            position_total = text_data["tcountu"][position]
            tag_count[corpus].setdefault(position, {})
            tag_percent[corpus].setdefault(position, {})

            tag_count[corpus][position].setdefault(position, [])
            tag_count[corpus][position][position].append(position_total)

            tag_percent[corpus][position].setdefault(position, [])
            tag_percent[corpus][position][position].append(
                position_total / sentences
                )

            for tag in TALLY_TAGS:
                tally = text_data["position_count"][position].get(tag) or 0
                tag_count[corpus][position].setdefault(tag, [])
                tag_percent[corpus][position].setdefault(tag, [])
                tag_count[corpus][position][tag].append(tally)
                tag_percent[corpus][position][tag].append( tally / sentences )


    for corpus in CORPORA:
        corpus_text_count = text_count[corpus]
        for position in POSITIONS:

            tag_avg_percent[corpus].setdefault(position, {})
            tag_total_count[corpus].setdefault(position, {})
            position_sum = sum(tag_percent[corpus][position][position])
            position_count = sum(tag_count[corpus][position][position])
            tag_total_count[corpus][position][position] = position_count
            tag_avg_percent[corpus][position][position] = position_sum / corpus_text_count
            if corpus == 'dps':
                tag_ttest.setdefault(position, {})
                tag_es.setdefault(position, {})
                tag_ttest[position][position] = ttest_1samp(
                    tag_percent[corpus][position][position],
                    tag_avg_percent['frantext'][position][position]
                    ).pvalue
                tag_es.setdefault(position, {})
                tag_es[position][position] = cohend(
                    tag_percent['dps'][position][position],
                    tag_percent['frantext'][position][position]
                    )

            for tag in TALLY_TAGS:
                tag_sum = sum(tag_percent[corpus][position][tag])
                tag_count_sum = sum(tag_count[corpus][position][tag])
                tag_total_count[corpus][position][tag] = tag_count_sum
                tag_avg_percent[corpus][position][tag] = tag_sum / corpus_text_count
                if corpus == 'dps':
                    tag_ttest[position][tag] = ttest_1samp(
                        tag_percent[corpus][position][tag],
                        tag_avg_percent['frantext'][position][tag]
                        ).pvalue
                    tag_es[position][tag] = cohend(
                        tag_percent['dps'][position][tag],
                        tag_percent['frantext'][position][tag]
                        )

    data = {
        'texts': texts,
        'sentences': sentence_count,
        'questions': question_count,
        'corpora': CORPORA,
        'positions': POSITIONS,
        'tally_tags': TALLY_TAGS,
        'tag_count': tag_count,
        'tag_percent': tag_percent,
        'tag_avg_percent': tag_avg_percent,
        'tag_total_count': tag_total_count,
        'tag_ttest': tag_ttest,
        'tag_es': tag_es
        }

    return render(request, 'all_dislocations.html', data)


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

