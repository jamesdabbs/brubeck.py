import logging

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

from brubeck.fields import SetField
from brubeck.models.wiki import Document, Revision
from brubeck.search import index_revision


logger = logging.getLogger(__name__)


class BaseSnippet(Document):
    """ A snippet is a revision-controlled blob of text describing a particular
        object in the database
    """
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')

    # This field stores meta-data about the snippet
    flags = SetField(max_length=255)

    class Meta:
        abstract = True
        app_label = 'brubeck'

    def current_text(self):
        """ Gets the most current & useful body of text for this snippet """
        return getattr(self.revision, 'text', '')


class Snippet(BaseSnippet):
    """ A plain (but non-abstract) snippet """
    class Meta:
        app_label = 'brubeck'


class Provable(models.Model):
    """ Subclassing Provable allows an object to hook into the automatic
        proof generation system.
    """
    proof_agent = models.CharField(max_length=255)

    # The snippet's revision-controlled text will store a dump of the proof
    # used to add this snippet, in a format understood and verifiable by the
    # proof agent. Since rendering a human-readable version of the proof may be
    # time-consuming, we'll also store a copy of that here:
    proof_text = models.TextField()

    class Meta:
        app_label = 'brubeck'
        abstract = True

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
        if self.proof_agent:
            prover = self._get_prover()
            return prover.render_html(getattr(self.revision, 'text', ''),
                space=space)
        return self.current_text()


def update_proof(sender, instance, created, **kwargs):
    """ After saving a new Revision for a proof, we'd like to update the stored
        `proof_text`
    """
    try:
        proof = instance.page.proof
        if proof.proof_agent:
            # The proof was automatically generated
            # Forcing a re-save will update the cached proof_text
            proof.save()
    except Proof.DoesNotExist:  # Nothing to update for base Snippets
        pass


class Proof(Snippet, Provable):
    """ Users / alternate proof agents may wish to provide alternative proofs
        for Traits or Implications.
    """
    class Meta:
        app_label = 'brubeck'

    def current_text(self):
        return self.proof_text

    def save(self, *args, **kwargs):
        # TODO: saving a new Snippet with initial Revision seems to cause a
        # (probably needlessly) large number of queries. Streamline it.
        # Retreive and cache the current revision
        text = getattr(self.revision, 'text', '')
        self.proof_text = self._get_prover().render_text(text)
        super(Proof, self).save(*args, **kwargs)

models.signals.post_save.connect(index_revision, Revision)
models.signals.post_save.connect(update_proof, Revision)
