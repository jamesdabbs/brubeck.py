from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

from brubeck.fields import SetField
from brubeck.models.wiki import Document


class BaseSnippet(Document):
    """ A snippet is a revision-controlled blob of text describing a particular
        object in the database
    """
    NEEDS_DESCRIPTION = 1

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')

    # This field stores meta-data about the snippet
    flags = SetField(max_length=255)

    class Meta:
        abstract = True
        app_label = 'brubeck'

    def __unicode__(self):
        return self.text()

    def save(self, *args, **kwargs):
        """ Updates the NEEDS_DESCRIPTION flag appropriately """
        if self.revision and self.revision.text:
            self.flags.discard(self.NEEDS_DESCRIPTION)
        else:
            self.flags.add(self.NEEDS_DESCRIPTION)
        super(BaseSnippet, self).save(*args, **kwargs)


class Snippet(BaseSnippet):
    """ A plain (but non-abstract) snippet
    """
    class Meta:
        app_label = 'brubeck'


class Provable(models.Model):
    """ Subclassing Provable allows an object to hook into the automatic
        proof generation system.
    """
    proof_agent = models.CharField(max_length=255)

    # This (de-normalized) field stores a copy of the text describing the proof
    proof_text = models.TextField()

    class Meta:
        app_label = 'brubeck'
        abstract = True

    def get_prover(self):
        """ Gets a Prover object that can reason about this proof and the way
            it was generated.
        """
        path, cls = self.proof_agent.rsplit('.', 1)
        m = __import__(path)
        for acc in path.split('.')[1:]:
            m = getattr(m, acc)
        return getattr(m, cls)

    def render_html(self):
        """ Defers display to the Prover object
        """
        if self.proof_agent:
            prover = self.get_prover()
            return prover.render_html(self.text())
        return self.text()

    def save(self, *args, **kwargs):
        if self.proof_agent:
            self.proof_text = self.get_prover().render_text(self.text())
        else:
            self.proof_text = self.text()
        super(Provable, self).save(*args, **kwargs)


class Proof(Snippet, Provable):
    """ Users / alternate proof agents may wish to provide alternative proofs
        for Traits or Implications.
    """
    class Meta:
        app_label = 'brubeck'
