from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Tag (models.Model):
    tag_text = models.CharField(max_length=200, primary_key=True)

class Range (models.Model):
    start = models.CharField(max_length=200)
    end = models.CharField(max_length=200)
    start_offset = models.IntegerField(default=0)
    end_offset = models.IntegerField(default=0)

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
    user = models.ForeignKey(User)
    action = models.CharField(
        max_length=6,
        choices=ACTION_CHOICES,
        default=READ
        )

class Annotation (models.Model):
    annotator_schema_version = models.CharField(max_length=10)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    quote = models.TextField()
    uri = models.CharField(max_length=3000)
    ranges = models.ManyToManyField(Range)
    user = models.ForeignKey(User)
    consumer = models.CharField(max_length=100)
    tags = models.ManyToManyField(Tag)
    permissions = models.ManyToManyField(Permission)
