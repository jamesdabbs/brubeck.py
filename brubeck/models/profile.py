from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.db.utils import DatabaseError


class Profile(models.Model):
    user = models.OneToOneField(User)

    class Meta:
        app_label = 'brubeck'

    def __unicode__(self):
        return self.user.username

    @models.permalink
    def get_absolute_url(self):
        return 'brubeck:profile', (self.user.username,), {}

    username = property(lambda s: s.user.username)


# Attach a Profile to every newly created User
def add_profile(sender, instance, created, raw, **kwargs):
    if created and not raw:
        # This can fail if brubeck is under south migration control and we're
        # adding an initial admin superuser.
        # TODO: add support for that case ^ (on postgres w/ transactions)
        Profile.objects.create(user=instance)
post_save.connect(add_profile, sender=User)
