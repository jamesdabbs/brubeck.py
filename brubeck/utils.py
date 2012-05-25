import logging

from brubeck.models.snippets import Proof, Snippet


logger = logging.getLogger(__name__)


def add_snippet(obj, text, user, is_proof=False, proof_agent=None):
    """ Creates a Proof (if `is_proof`) or a general Snippet attached to this
        object, and creates a Revision by `user` with the given `text`
    """
    # The object must be saved before creating a snippet pointing to it
    if not obj.id:
        obj.save()
    cls = Proof if is_proof else Snippet
    snippet = cls(object=obj)
    if proof_agent:
        snippet.proof_agent = proof_agent
    snippet.save()
    snippet.add_revision(text=text, user=user)


def check_consistency():
    """ Checks the entire database for consistency. """
    from brubeck.models import Implication

    errors = 0
    for i in Implication.objects.all():
        cx = i.counterexamples()
        if cx.exists():
            errors += 1
            logger.error('Found counterexamples to (%s) %s: %s' %\
                (i.id, i, cx))
    if errors:
        logger.error('Found %s implications with counterexamples.' % errors)
    else:
        logger.error('No errors found.')


def mark_incomplete_snippets():
    """ Marks snippets with no text in their revision as needing improvement.
    """
    INC = Snippet.NEEDS_DESCRIPTION
    for s in Snippet.objects.all():
        if s.revision.text:
            if INC in s.flags:
                s.flags.discard(INC)
                s.save()
        else:
            s.flags.add(INC)
            s.save()
            logger.debug('Marked %s as needing description.' % s.object)


def get_incomplete_snippets():
    """ Gets snippets which need improved descriptions. """
    return Snippet.objects.filter(flags__contains='|%s|' % \
                                                  Snippet.NEEDS_DESCRIPTION)

def get_open_converses():
    """ Finds implications with open converses. """
    # TODO: exclude known reversible implications
    from brubeck.models.provable import Implication
    return filter(lambda i: not i.converse().counterexamples().exists(),
        Implication.objects.all())