from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from taggit.managers import TaggableManager

class Permission(models.Model):
    READ = 'read'
    UPDATE = 'update'
    DELETE = 'delete'
    ADMIN = 'admin'
    ACTION_CHOICES = {
        (READ, READ),
        (UPDATE, UPDATE),
        (DELETE, DELETE),
        (ADMIN, ADMIN)
        }
    django_user = models.ForeignKey(User)
    action = models.CharField(
        max_length=6,
        choices=ACTION_CHOICES,
        default=READ
        )

class Annotation (models.Model):
    annotator_schema_version = models.CharField(max_length=10, default='2.0.0')
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    text = models.TextField(db_index=True)
    quote = models.TextField(blank=True, null=True)
    uri = models.CharField(max_length=3000, null=True)
    tags = TaggableManager()
    django_user = models.ForeignKey(User, db_index=True)
    consumer = models.CharField(max_length=100, default='Annotator')
    permissions = models.ManyToManyField(Permission)

class Range (models.Model):
    start = models.CharField(max_length=200)
    end = models.CharField(max_length=200)
    startOffset = models.IntegerField(default=0)
    endOffset = models.IntegerField(default=0)
    annotation = models.ForeignKey(
        Annotation,
        related_name='ranges',
        on_delete=models.CASCADE
        )
