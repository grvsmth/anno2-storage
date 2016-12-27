from django import forms

from .models import Tag, Range, Permission, Annotation

class TagForm (forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['tag_text']

class RangeForm(forms.ModelForm):
    class Meta:
        model = Range
        fields = ['start', 'end', 'start_offset', 'end_offset']

class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = ['user', 'action']

class AnnotationForm (forms.ModelForm):
    class Meta:
        model = Annotation
        fields = [
            'annotator_schema_version',
            'text',
            'quote',
            'uri',
            'ranges',
            'user',
            'consumer',
            'tags',
            'permissions'
            ]