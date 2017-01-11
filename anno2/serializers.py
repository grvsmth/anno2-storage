import logging
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Annotation, Range

LOG = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email')

class RangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Range
        fields = ('start', 'end', 'start_offset', 'end_offset')

class AnnotationSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(label='ID')
    ranges = RangeSerializer(many=True)

    def create(self, validated_data):
        LOG.error(validated_data)

        range_data = validated_data.pop('ranges')
        annotation = Annotation.objects.create(django_user=self.context['request'].user, **validated_data)
        for range_datum in range_data:
            Range.objects.create(annotation=annotation, **range_datum)

        return annotation
    class Meta:
        model = Annotation
        fields = ('id', 'text', 'quote', 'uri', 'ranges')
