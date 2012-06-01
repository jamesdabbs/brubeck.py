# Provides several utilities for working with formulae
import logging

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from brubeck.logic import Formula
from brubeck.models import Space, Value
from brubeck.utils import add_snippet


logger = logging.getLogger(__name__)

proof_agent = 'brubeck.logic.prover.Prover'


def _intersection(ls):
    """ (Efficiently?) finds the intersection of a list of lists """
    # The python implementation of set intersection uses hashes, so this should
    # be relatively fast, but could probably made faster using the assumption
    # that each list in ls is already sorted
    return sorted(list(reduce(set.intersection, (set(l) for l in ls))))


def _union(ls):
    """ (Efficiently?) finds the union of a list of lists """
    from heapq import merge
    return merge(*ls)


def spaces_matching_formula(formula, evaluates_to=True,
                            spaces=Space.objects.all()):
    """ Finds the ids of Spaces for which the given formula evaluates to the
        given value.

        `spaces` is a queryset of Spaces from which to filter.
    """
    # For convenience (and to avoid ridiculous nested SQL queries), we only
    # query on the atoms and build the result in python.
    if formula.is_atom():
        p, v = formula.property, formula.value
        if not p or not v:
            return []
        spaces = spaces.order_by('id').values('id')
        if evaluates_to:
            spaces = spaces.filter(trait__property__id=p, trait__value__id=v)
        elif evaluates_to is None:
            spaces = spaces.exclude(trait__property__id=p)
        else:
            spaces = spaces.filter(trait__property__id=p,
                trait__value__id=Value.NOT[v])
        return [d['id'] for d in spaces]
    else:
        subs = (spaces_matching_formula(sf, evaluates_to, spaces)
            for sf in formula.sub)
        if formula.operator == Formula.AND:
            if evaluates_to:
                # An &'d formula evaluates to True if every subformula is True
                spaces = _intersection(subs)
            else:
                # An &'d formula evaluates to False if any subformula is False
                # (and so is unknown if any is unknown)
                spaces = _union(subs)
        elif formula.operator == Formula.OR:
            if evaluates_to:
                # An |'d formula evaluates to True if any subformula is True
                spaces = _union(subs)
            else:
            # An |'d formula evaluates to True if any subformula is True
                spaces = _intersection(subs)
    return spaces


def _find_spaces(implication, ant_val, cons_val, spaces):
    """ Utility function for finding spaces with various relations to an
        implication.
    """
    return Space.objects.filter(id__in=_intersection((
        spaces_matching_formula(implication.antecedent, spaces=spaces,
            evaluates_to=ant_val),
        spaces_matching_formula(implication.consequent, spaces=spaces,
            evaluates_to=cons_val)
        )))


def find_proofs(implication, spaces=Space.objects.all()):
    """ Returns Spaces for which this Implication can prove new Traits """
    return _find_spaces(implication, True, None, spaces)


def find_contra_proofs(implication, spaces=Space.objects.all()):
    """ Returns Spaces for witch the contrapositive of this Implication can
        prove new Traits
    """
    return _find_spaces(implication, None, False, spaces)


def examples(implication, spaces=Space.objects.all()):
    """ Returns examples where this Implication holds """
    return _find_spaces(implication, True, True, spaces)


def counterexamples(implication, spaces=Space.objects.all()):
    """ Returns examples where this Implication does not hold (should return
        [] for any saved Implication)
    """
    return _find_spaces(implication, True, False, spaces)


def verify_match(formula, space):
    """ Verifies that the given formula evaluates to True on the given Space,
        and returns a list of Traits demonstrating such. Raises an
        AssertionError if the Space does not match as claimed.
    """
    # TODO: we can get this down to one query by pre-fetching all the relevant
    #       traits and storing them in a python list for the duration of this
    #       function. Is this improvement significant? (Is it an improvement?)
    try:
        if formula.is_atom():
            rv = [space.trait_set.get(property__id=formula.property,
                value__id=formula.value)]
        else:
            rv = []
            if formula.operator == Formula.AND:
                # Adjoin proofs that all subformulae match
                for sf in formula.sub:
                    rv += verify_match(sf, space)
            else:  # formula.operator == Formula.OR
                found = False
                for sf in formula.sub:
                    # We only need to find one subformula that matches, but
                    # should check for the possibility that none do.
                    try:
                        rv += verify_match(sf, space)
                        found = True
                        break
                    except AssertionError:
                        continue
                if not found:
                    raise AssertionError('%s did not match the formula (%s)' %
                        (space, formula))
        return rv
    except ObjectDoesNotExist:
        raise AssertionError('%s did not match the given formula (%s)' %
            (space, formula))


def force_match(formula, space, proof_steps):
    """ Forces the given Space to match the formula by adding Traits as needed.

        `proof_steps` are added to the start of the automatically generated
        proof, and should consist of a list of Traits and Implications.
    """
    if formula.is_atom():
        ts = space.trait_set.filter(property__id=formula.property)
        if ts.exists():
            if unicode(ts.get().value.id) == formula.value:
#                logger.warn(u'%s already matches for %s' % (formula, space))
                pass
            else:
                raise AssertionError(u'%s cannot match %s' % (formula, space))
        else:
            add_proof(space=space, property_id=formula.property,
                value_id=formula.value, proof_steps=proof_steps)
    elif formula.operator == Formula.AND:
        for sf in formula.sub:
            force_match(sf, space, proof_steps)
    else:  # formula.operator == Formula.OR
        # Verify that the negation of all but one subformula matches
        unknown_sf = None
        extra_steps = []
        for sf in formula.sub:
            try:
                extra_steps += verify_match(sf.negate(), space)
            except AssertionError:
                # This subformula has an unknown value
                if unknown_sf:  # We have multiple unknown subformulae
                    raise AssertionError(u'Tried to force an OR statement '
                        u'multiple unknowns (%s)' % formula)
                unknown_sf = sf
        if unknown_sf:  # The single (formerly) unknown must be true
            force_match(unknown_sf, space, proof_steps + extra_steps)
        else:
            raise AssertionError(u'Tried to force OR statement with '
                                 u'no unknowns (%s)' % formula)


def prove(implication, space):
    """ Applies the Implication to the Space, adding new Traits (with proofs)
        if possible.
    """
    # First we verify that the space matches (each part of) the antecedent
    proof_steps = verify_match(formula=implication.antecedent, space=space)
    proof_steps.append(implication)
    force_match(formula=implication.consequent, space=space,
        proof_steps=proof_steps)


def prove_contrapositive(implication, space):
    """ Applies the contrapositive of the Implication to the Space, similar
        to prove(implication, space)
    """
    proof_steps = verify_match(formula=implication.consequent.negate(),
        space=space)
    proof_steps.append(implication)
    force_match(formula=implication.antecedent.negate(), space=space,
        proof_steps=proof_steps)


def add_proof(space, property_id, value_id, proof_steps):
    """ A proof is simply a series of Traits or Implications formatted as:
        t<id>,t<id>,i<id>,t<id>,t<id>,...
    """
    from brubeck.models import Trait

    brubeck_user, _ = User.objects.get_or_create(username='brubeck')

    proof_string = ''
    for s in proof_steps:
        if isinstance(s, Trait):
            proof_string += 't%s,' % s.id
        else:  # s is an Implication
            proof_string += 'i%s,' % s.id
    t = Trait(space=space)
    t.property_id, t.value_id = property_id, value_id
    t.save()
    add_snippet(t, text=proof_string, user=brubeck_user, is_proof=True,
        proof_agent=proof_agent)
    logger.debug('Added trait "%s" with proof "%s"' % (t, proof_string))


def _add_proofs():
    """ Utility function to extrapolate existing Traits as far as possible.
    """
    from brubeck.models import Implication

    for i in Implication.objects.all():
        for s in find_proofs(i):
            try:
                prove(implication=i, space=s)
            except Exception as e:
                logger.debug('(%s|%s) %s' % (i.id, s.id, e))
        for s in find_contra_proofs(i):
            try:
                prove_contrapositive(implication=i, space=s)
            except Exception as e:
                logger.debug('(%s|%s) %s' % (i.id, s.id, e))


def apply(implication, space):
    """ Applies the Implication to the Space, deducing new Traits if
        possible.
    """
    try:
        prove(implication, space)
    except AssertionError as e:
        pass
    try:
        prove_contrapositive(implication, space)
    except AssertionError as e:
        pass


# This counts the number of proof visualization nodes that have been rendered,
# so that each gets a unique id
node_count = 0


def get_full_proof(trait):
    from brubeck.models import Trait

    # TODO: restructure JSON to produce adjacencies, arrows
    # TODO: using a global feels so dirty :(

    # Every proof will include the node proved
    global node_count
    node_count += 1
    data = [{
        "id": "t%s_%s" % (trait.id, node_count),
        "name": trait.name_without_space(),
        'adjacencies': []
    }]

    # If the proof was automatically added, we also add an implication and
    # the full proof of each trait it needed to assume.
    proof = trait.snippets.exclude(proof=None).exclude(proof__proof_agent='')
    if proof.exists():
        assumptions = proof[0].revision.text.split(',')
        traits, implication = [], None
        # There should be a trailing comma / empty last assumption
        assert not assumptions[-1]
        for a in assumptions[:-1]:
            if a[0] == 't':
                traits.append(Trait.objects.get(id=int(a[1:])))
        for t in traits:
            pd = get_full_proof(t)
            pd[0]['adjacencies'] = [{
                'nodeTo': data[0]['id']
            }]
            data += pd

        data[0].update({
            'data': {'text': proof[0].proof.render_html(space=False),
                     'url': trait.get_absolute_url()}
        })
    else:
        data[0].update({
            'data': {'text': trait.snippets.all()[0].current_text(),
                     'url': trait.get_absolute_url()}
        })

    return data
