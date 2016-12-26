from django.db import models
from django.contrib.auth.models import User

class Tag (models.Model):
    tag_text = models.CharField(max_length=200, primary_key=True)

class Range (models.Model):
    start = models.CharField(max_length=200)
    end = models.CharField(max_length=200)
    startOffset = models.IntegerField(default=0)
    endOffset = models.IntegerField(default=0)

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
