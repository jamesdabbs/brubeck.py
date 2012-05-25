from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save

class Profile(models.Model):
    user = models.OneToOneField(User)

    class Meta:
        app_label = 'brubeck'

# Attach a Profile to every newly created User
def add_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

post_save.connect(add_profile, sender=User)