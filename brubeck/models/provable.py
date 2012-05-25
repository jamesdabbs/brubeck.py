# -*- encoding: utf-8 -*-
from django.contrib.contenttypes import generic
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query_utils import Q
from django.db.models.signals import post_save
from django.utils.safestring import mark_safe

from brubeck.logic import prover, utils
from brubeck.logic.formula import FormulaField, atomize
from brubeck.models import Space, Property


# TODO: add title methods which produce (safe) html output w/ links

class _ProvesTraitMixin(models.Model):
    traits = lambda o: prover.Prover.implied_traits(o)
    traits_desc = 'Related Traits'

    class Meta:
        abstract = True

class Trait(_ProvesTraitMixin):
    """ A Trait records whether a Space has a particular Property """
    space = models.ForeignKey(Space)
    property = models.ForeignKey(Property)
    value = models.ForeignKey('Value')
    snippets = generic.GenericRelation('Snippet')

    class Meta:
        app_label = 'brubeck'

    def __unicode__(self):
        return u'%s: %s' % (self.space, atomize(self.property, self.value))
    name = __unicode__

    def title(self):
        """ Adds HTML links to this object's title
        """
        return mark_safe('<a href="%s">%s</a>: <a href="%s">%s</a>' % (
            self.space.get_absolute_url(), self.space,
            self.property.get_absolute_url(), atomize(self.property, self.value)
        ))

    @models.permalink
    def get_absolute_url(self):
        return 'trait', (), {'space': self.space.slug,
                             'property': self.property.slug}

    @models.permalink
    def get_edit_url(self):
        return 'edit_trait', (), {'space': self.space.slug,
                                  'property': self.property.slug}

def trait_post_save(sender, instance, created, **kwargs):
    """ Checks all implications involving this property for new proofs.
    """
    if created:
        # TODO: improve formula field lookups. This is overly broad. `contains='1='` matches '31=True' as well.
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
    snippets = generic.GenericRelation('Snippet')

    class Meta:
        app_label = 'brubeck'

    def save(self, *args, **kwargs):
        if kwargs.get('commit', True) and self.counterexamples().exists():
            raise ValidationError('Cannot save implication with known counterexamples: %s' % self.counterexamples())
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
    def get_absolute_url(self):
        return 'implication', (), {'id': self.id}

    @models.permalink
    def get_edit_url(self):
        return 'edit_implication', (), {'id': self.id}

    def contrapositive(self):
        """ Constructs the logically equivalent contrapositive of this
            implication.
        """
        return Implication(
            antecedent=self.consequent.negate(),
            consequent=self.antecedent.negate()
        )

    def converse(self):
        """ Constructs the logical converse of this implication.
        """
        return Implication(
            antecedent=self.consequent,
            consequent=self.antecedent
        )

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
    """ Checks all implications involving this property for new proofs.
    """
    if created:
        for s in instance.find_proofs():
            utils.apply(instance, s)
post_save.connect(implication_post_save, Implication)