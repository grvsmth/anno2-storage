import logging
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Annotation

LOG = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email')

class AnnotationSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(label='ID')
    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username'
        )
    def create(self, validated_data):
        LOG.error(validated_data)
        """
        user_data = validated_data.pop('user')
        LOG.error(user_data)
        django_user = User.objects.get(username=user_data)
        validated_data['django_user'] = django_user
        LOG.error(validated_data)
        """
        return validated_data
    class Meta:
        model = Annotation
        fields = (['id', 'text', 'quote', 'uri', 'user'])
