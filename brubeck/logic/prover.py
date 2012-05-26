# Defines the native Prover class, the API to automatic proof generation
from django.utils.safestring import mark_safe


class Prover(object):
    """ The Prover class is the public interface to automatic proof generation.
        It should implement the following classmethods (with hopefully clear
        purposes).
        - check_proof(cls, proof)
        - find_proofs(cls, spaces, implications, add)
        - render_html(cls, proof)
    """
    @classmethod
    def check_proof(cls, proof):
        raise NotImplementedError()

    @classmethod
    def find_proofs(cls, spaces=None, implications=None, add=True):
        raise NotImplementedError()

    @classmethod
    def _render(cls, proof, html):
        """ Takes a proof of the form t<id>,t<id>,i<id>,t<id>,... and formats
            it suitably for template output.
        """
        from brubeck.models import Trait, Implication

        rv = ''
        for s in proof.split(',')[:-1]:
            type, id = s[0], s[1:]
            if type == 't':
                obj = Trait.objects.get(id=id)
                name = unicode(obj)
            else: # type == 'i'
                obj = Implication.objects.get(id=id)
                name = obj.__unicode__(lookup=True)
            if html:
                rv += u'<a href="%s">%s</a><br/>' % (obj.get_absolute_url(), name)
            else:
                rv += u'%s, ' % name
        return mark_safe(rv)

    @classmethod
    def render_html(cls, proof):
        return cls._render(proof, html=True)

    @classmethod
    def render_text(cls, proof):
        return cls._render(proof, html=False)

    @classmethod
    def implied_traits(cls, obj):
        from brubeck.models import Trait

        ident = '%s%s,' % (obj.__class__.__name__[0].lower(), obj.id)
        return Trait.objects.filter(snippets__revision__text__contains=ident)