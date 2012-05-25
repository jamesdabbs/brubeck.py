# Contains descriptions of wiki-style revision controlled documents
# Nothing in this file should reference Brubeck-specific models, so this should
#   be suitable for spinning off into a standalone app if needed.
from django.contrib.auth.models import User
from django.db import models


class Document(models.Model):
    """ Represents a page or document in the Wiki, along with all its
        associated meta-data
    """
    MAIN = 0
    TALK = 1
    NS_CHOICES = (
        (MAIN, 'Main'),
        (TALK, 'Talk')
        )
    title = models.CharField(max_length=255)
    restrictions = models.CharField(max_length=255)
    last_touched = models.DateTimeField(auto_now=True)
    revision = models.ForeignKey('Revision',
        null=True) # Latest will be null, but only while creating a new page
    namespace = models.IntegerField(choices=NS_CHOICES, default=MAIN)

    class Meta:
        app_label = 'brubeck'

    def add_revision(self, text, user):
        """ Utility method to allow `user` to submit a revision with the given
            `text`.
        """
        r = Revision.objects.create(
            page=self, text=text, user=user, parent=self.revision)
        self.revision = r
        self.save()

    def current_revision(self):
        """ Returns the most recently added Revision for this Document. """
        # TODO: do we need both this and the revision FK?
        # Consider how to handle deletions, non-reviewed edits, etc.
        return self.revisions.order_by('-timestamp')[0]

    def text(self):
        """ Gets the text of the current Revision. """
        return self.current_revision().text


class Revision(models.Model):
    """ Represents a single revision of a Page, along with author and
        other meta-data
    """
    page = models.ForeignKey('Document', related_name='revisions')
    text = models.TextField()
    # Commit information
    user = models.ForeignKey(User)
    comment = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True)

    class Meta:
        app_label = 'brubeck'

    def __unicode__(self):
        return self.text