from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Annotation

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email')

class AnnotationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Annotation
        fields = (
            'annotator_schema_version',
            'text',
            'quote',
            'uri',
            'ranges',
            'user',
            'consumer',
            'tags',
            'permissions'
            )