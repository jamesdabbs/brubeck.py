from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.db.utils import DatabaseError


class Profile(models.Model):
    user = models.OneToOneField(User)

    class Meta:
        app_label = 'brubeck'


# Attach a Profile to every newly created User
def add_profile(sender, instance, created, **kwargs):
    if created:
        try:
            Profile.objects.create(user=instance)
        # This can fail if brubeck is under revision control and we're adding
        # an initial admin superuser.
        except DatabaseError as e:
            print 'Unable to save a profile for user %s: %s' % (instance, e)
post_save.connect(add_profile, sender=User)
