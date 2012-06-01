import logging

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

from brubeck.fields import SetField
from brubeck.models.wiki import Document, Revision
from brubeck.search import index_revision


logger = logging.getLogger(__name__)


class Snippet(Document):
    """ A snippet is a revision-controlled blob of text describing a particular
        object in the database
    """
    USER = 'user'

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')

    # This field stores meta-data about the snippet
    flags = SetField(max_length=255)

    # Proof-related information
    proof_agent = models.CharField(max_length=255)
    proof_text = models.TextField()

    class Meta:
        app_label = 'brubeck'

    def is_proof(self):
        """ Determines whether this snippet represents a complete proof """
        return self.proof_agent != ''

    def automatically_added(self):
        return self.proof_agent and self.proof_agent != self.USER

    def current_text(self):
        """ Gets the most current & useful body of text for this snippet """
        return self.proof_text if self.is_proof() else \
            getattr(self.revision, 'text', '')

    def _get_prover(self):
        """ Gets a Prover object that can reason about this proof and the way
            it was generated.
        """
        path, cls = self.proof_agent.rsplit('.', 1)
        m = __import__(path)
        for acc in path.split('.')[1:]:
            m = getattr(m, acc)
        return getattr(m, cls)

    def render_html(self, space=True):
        """ Uses the module that added this proof to build a human-readable
            proof with links to the assumed facts.
        """
        if self.automatically_added():
            prover = self._get_prover()
            return prover.render_html(getattr(self.revision, 'text', ''),
                space=space)
        return self.current_text()

    def save(self, *args, **kwargs):
        # TODO: saving a new Snippet with initial Revision seems to cause a
        # (probably needlessly) large number of queries. Streamline it.
        # Retreive and cache the current revision
        if self.automatically_added():
            text = getattr(self.revision, 'text', '')
            self.proof_text = self._get_prover().render_text(text)
        super(Snippet, self).save(*args, **kwargs)


def update_proof(sender, instance, created, **kwargs):
    """ After saving a new Revision for a proof, we'd like to update the stored
        `proof_text`
    """
    try:
        snippet = instance.page.snippet
        if snippet.automatically_added():
            # Forcing a re-save will update the cached proof_text
            snippet.save()
    except Snippet.DoesNotExist:  # Nothing to update for base Snippets
        pass
    except Exception as e:
        logger.debug('Error updating proof for %s: %s' % (instance, e))


models.signals.post_save.connect(index_revision, Revision)
models.signals.post_save.connect(update_proof, Revision)
