import logging
from django.contrib.auth.models import User
from rest_framework import serializers
from taggit_serializer.serializers import (
    TagListSerializerField,
    TaggitSerializer
    )
from .models import Annotation, Range

LOG = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email')

class RangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Range
        fields = ('start', 'end', 'startOffset', 'endOffset')

class AnnotationSerializer(TaggitSerializer, serializers.ModelSerializer):

    id = serializers.ReadOnlyField(label='ID')
    ranges = RangeSerializer(many=True)
    tags = TagListSerializerField()

    def create(self, validated_data):
        to_be_tagged, validated_data = self._pop_tags(validated_data)
        LOG.debug(validated_data)
        range_data = validated_data.pop('ranges')

        annotation = Annotation.objects.create(
            django_user=self.context['request'].user,
            **validated_data
            )
        for range_datum in range_data:
            Range.objects.create(annotation=annotation, **range_datum)
        self._save_tags(annotation, to_be_tagged)

        return annotation

    def update(self, instance, validated_data):
        LOG.error(validated_data)
        to_be_tagged, validated_data = self._pop_tags(validated_data)
        range_data = validated_data.pop('ranges')
        instance.quote = validated_data.get('quote', instance.quote)
        instance.text = validated_data.get('text', instance.text)
        instance.uri = validated_data.get('uri', instance.uri)
        # delete all ranges and recreate them
        Range.objects.filter(annotation=instance).delete()
        for range_datum in range_data:
            Range.objects.create(annotation=instance, **range_datum)
        self._save_tags(instance, to_be_tagged)
        instance.save()
        return instance

    class Meta:
        model = Annotation
        fields = ('id', 'text', 'quote', 'uri', 'ranges', 'tags')
