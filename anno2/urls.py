"""anno2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers

from . import views

router = routers.SimpleRouter(trailing_slash=False)
router.register(r'users', views.UserViewSet)
router.register(r'annotations', views.AnnotationViewSet, 'Annotation')
router.register(r'search', views.SearchViewSet, 'Search')

urlpatterns = [
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^stage', views.repanix, name='repanix'),
    url(r'^auth/token$', views.token, name='token'),
    url(r'^store/', include(router.urls)),
    url(r'^profile/', views.profile, name='profile'),
    url(r'^save/', views.save_anno, name='save'),
    url(
        r'^api-auth/',
        include('rest_framework.urls', namespace='rest_framework')
        ),
    url(r'^anno2.js$', views.jsfile, name='jsfile'),
    url(r'', views.root, name='root')
]
