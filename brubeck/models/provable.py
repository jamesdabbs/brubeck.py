# -*- encoding: utf-8 -*-
from django.contrib.contenttypes import generic
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query_utils import Q
from django.db.models.signals import post_save
from django.utils.html import escape
from django.utils.safestring import mark_safe

from brubeck.logic import prover, utils
from brubeck.logic.formula import FormulaField, atomize
from brubeck.models import Space, Property


class _ProvesTraitMixin(models.Model):
    traits = lambda o: prover.Prover.implied_traits(o)
    traits_desc = 'Related Traits'

    class Meta:
        abstract = True

    @property
    def snippets(self):
        # workaround for this bug: http://code.djangoproject.com/ticket/12728
        # replies = generic.GenericRelation(ThreadedComment)
        from django.contrib.contenttypes.models import ContentType
        from brubeck.models.snippets import Snippet
        type = ContentType.objects.get_for_model(self)
        return Snippet.objects.filter(content_type__pk=type.id,
            object_id=self.id)


class Trait(_ProvesTraitMixin):
    """ A Trait records whether a Space has a particular Property """
    space = models.ForeignKey(Space)
    property = models.ForeignKey(Property)
    value = models.ForeignKey('Value')

    class Meta:
        app_label = 'brubeck'
        unique_together = (('space', 'property'),)

    def __unicode__(self, space=True):
        pref = u'%s: ' % self.space if space else ''
        return u'%s%s' % (pref, atomize(self.property, self.value))
    name = __unicode__

    def title(self, space=True):
        """ Renders this Trait's name with links added """
        pref = '<a href="%s">%s</a>: ' % (self.space.get_absolute_url(),
            escape(self.space)) if space else ''
        return mark_safe('%s<a href="%s">%s</a>' % (pref,
            self.property.get_absolute_url(),
            atomize(escape(self.property), self.value)
        ))
    name_without_space = lambda t: t.__unicode__(space=False)

    def name_without_property(self):
        return atomize(self.space, self.value)

    @models.permalink
    def get_absolute_url(self, type=''):
        return 'brubeck:%strait' % type, (), {'space': self.space.slug,
                                      'property': self.property.slug}

    get_edit_url = lambda x: Trait.get_absolute_url(x, 'edit_')
    get_proof_url = lambda x: Trait.get_absolute_url(x, 'prove_')
    get_delete_url = lambda x: Trait.get_absolute_url(x, 'delete_')
    get_revision_url = lambda x: Trait.get_absolute_url(x, 'revise_')

    @models.permalink
    def get_admin_url(self):
        return 'admin:brubeck_trait_change', (self.id,), {}


def trait_post_save(sender, instance, created, **kwargs):
    """ Checks all implications involving this property for new proofs. """
    if created:
        # TODO: improve formula field lookups. This is overly broad, e.g.
        #       `contains='1='` matches '31=True' as well.
        # TODO: factor in to Prover class
        pid = '%s=' % instance.property.id
        candidate_imps = Implication.objects.filter(
            Q(antecedent__contains=pid) | Q(consequent__contains=pid))
        for i in candidate_imps:
            utils.apply(i, instance.space)
post_save.connect(trait_post_save, Trait)


class Implication(_ProvesTraitMixin):
    """ An Implication allows us to deduce new properties from old ones. """
    antecedent = FormulaField()
    consequent = FormulaField()

    # Marks whether an implication is actually an equivalence
    # TODO: should this have an FK to the converse? Is there a good general way
    # to find converses? Don't forget that A + B != B + A for formulae
    reverses = models.BooleanField(default=False)

    class Meta:
        app_label = 'brubeck'

    def save(self, *args, **kwargs):
        if kwargs.get('commit', True) and self.counterexamples().exists():
            raise ValidationError('Cannot save implication with known '
                'counterexamples: %s' % self.counterexamples())
        super(Implication, self).save(*args, **kwargs)

    def __unicode__(self, **kwargs):
        ant = self.antecedent.__unicode__(**kwargs)
        cons = self.consequent.__unicode__(**kwargs)
        return u'%s ⇒ %s' % (ant, cons)

    def name(self):
        return self.__unicode__(lookup=True, link=False)

    def title(self):
        return mark_safe(self.__unicode__(lookup=True, link=True))

    @models.permalink
    def get_absolute_url(self, type=''):
        return 'brubeck:%simplication' % type, (), {'id': self.id}

    get_edit_url = lambda x: Implication.get_absolute_url(x, 'edit_')
    get_proof_url = lambda x: Implication.get_absolute_url(x, 'prove_')
    get_delete_url = lambda x: Implication.get_absolute_url(x, 'delete_')
    get_revision_url = lambda x: Implication.get_absolute_url(x, 'revise_')

    @models.permalink
    def get_admin_url(self):
        return 'admin:brubeck_implication_change', (self.id,), {}

    def contrapositive(self):
        """ Constructs the logically equivalent contrapositive of this
            implication.
        """
        return Implication(antecedent=self.consequent.negate(),
            consequent=self.antecedent.negate())

    def converse(self):
        """ Constructs the logical converse of this implication. """
        return Implication(antecedent=self.consequent,
            consequent=self.antecedent)

    def find_proofs(self):
        """ Finds Spaces that this Implication can prove something new about.
        """
        return utils.find_proofs(self)

    def examples(self):
        """ Finds Spaces for which this Implication holds. """
        return utils.examples(self)

    def counterexamples(self):
        """ Finds Spaces for which this Implication does not hold. This should
            always return [] for any saved Implication.
        """
        return utils.counterexamples(self)


def implication_post_save(sender, instance, created, **kwargs):
    """ Checks all implications involving this property for new proofs. """
    if created:
        for s in instance.find_proofs():
            utils.apply(instance, s)
        for s in instance.contrapositive().find_proofs():
            utils.apply(instance, s)
post_save.connect(implication_post_save, Implication)

# TODO: allow post_save options to be asynchronous (w/ celery)
# TODO: improve post-delete handling (delete revisions from index, related
#       traits, etc.)
