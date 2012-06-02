import logging

from brubeck.models.snippets import Snippet
from brubeck.models.core import Space


logger = logging.getLogger(__name__)


def check_consistency():
    """ Checks the entire database for consistency. """
    from brubeck.models import Implication

    errors = []
    for i in Implication.objects.all():
        cx = i.counterexamples()
        if cx.exists():
            errors.append((i, cx))
    if errors:
        logger.error('Found implications with counterexamples.' % errors)
    else:
        logger.debug('No errors found.')
    return errors


def get_incomplete_snippets():
    """ Gets snippets which need improved descriptions. """
    return Snippet.objects.filter(revision__text='')


def get_open_converses():
    """ Finds implications with open converses. """
    from brubeck.models.provable import Implication
    return filter(lambda i: not i.converse().counterexamples().exists(),
        Implication.objects.exclude(reverses=True))


def get_unknown_spaces(property):
    """ Finds spaces for which this Property's value is unknown """
    return Space.defined_objects.exclude(trait__property=property)


def get_orphans(t):
    """ Returns all traits that would have no proof if `t` were deleted """
    # TODO: only include if no other proof exists
    # TODO: better handling of multiple snippets / proofs
    from brubeck.logic.prover import Prover
    direct = Prover.implied_traits(t)
    subs = [get_orphans(s) for s in direct]
    return list(direct) + sum(subs, [])
