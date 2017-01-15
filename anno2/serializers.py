import logging
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Annotation, Range, Tag

LOG = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('tag_text',)

class RangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Range
        fields = ('start', 'end', 'startOffset', 'endOffset')

class ReplaceMe():
    def to_internal_value(self, data):
        LOG.error(data)
        tag_data = data.get('tags', [])
        tag_dicts = []
        for tag_datum in tag_data:
            tag_dicts.append({'tag_text': tag_datum})
        data['tags'] = tag_dicts
        return data

class AnnotationSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(label='ID')
    ranges = RangeSerializer(many=True)
    tags = TagSerializer(many=True)

    def create(self, validated_data):
        LOG.debug(validated_data)
        range_data = validated_data.pop('ranges')
        tag_data = validated_data.pop('tags')

        annotation = Annotation.objects.create(django_user=self.context['request'].user, **validated_data)
        for range_datum in range_data:
            Range.objects.create(annotation=annotation, **range_datum)
        tag_objs = []
        for tag_datum in tag_data:
            tag, created = Tag.objects.get_or_create(tag_text=tag_datum['tag_text'])
            tag_objs.append(tag)
        annotation.tags = tag_objs
        annotation.save()

        return annotation

    def update(self, instance, validated_data):
        LOG.error(validated_data)
        LOG.error(instance.text)
        range_data = validated_data.pop('ranges')
        tag_data = validated_data.pop('tags')
        instance.quote = validated_data.get('quote', instance.quote)
        instance.text = validated_data.get('text', instance.text)
        instance.uri = validated_data.get('uri', instance.uri)
        # delete all ranges and recreate them
        Range.objects.filter(annotation=instance).delete()
        for range_datum in range_data:
            Range.objects.create(annotation=instance, **range_datum)
        new_tags = []
        for tag_datum in tag_data:
            tag, created = Tag.objects.get_or_create(tag_text=tag_datum['tag_text'])
            new_tags.append(tag)
        instance.tags = new_tags
        instance.save()
        return instance

    def get_tags(self, annotation):
        return annotation.tags.values_list('tag_text', flat=True)

    class Meta:
        model = Annotation
        fields = ('id', 'text', 'quote', 'uri', 'ranges', 'tags')
