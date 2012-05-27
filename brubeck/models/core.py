# -*- coding: utf-8 -*-
from django.contrib.contenttypes import generic
from django.db import models
from django.template.defaultfilters import slugify


class ValueSet(models.Model):
    """ Represents a collection of values - booleans, cardinals, &c. """
    BOOLEAN = 1

    name = models.CharField(max_length=255, unique=True)

    class Meta:
        app_label = 'brubeck'

    __unicode__ = lambda o: unicode(o.name)


class Value(models.Model):
    """ Represents a single value - True (boolean), ω (cardinal), &c. """
    TRUE = 1
    FALSE = 2
    NOT = {
        TRUE: FALSE,
        unicode(TRUE): FALSE,
        FALSE: TRUE,
        unicode(FALSE): TRUE,
    }

    name = models.CharField(max_length=255)
    value_set = models.ForeignKey('ValueSet', related_name='values')

    class Meta:
        app_label = 'brubeck'
        unique_together = (('name', 'value_set'),)

    __unicode__ = lambda o: unicode(o.name)

    def table_display(self):
        """ Formats the value for display in the summary table """
        return {
            'True': '+',
            'False': '-'
        }.get(self.name, '')

    @classmethod
    def negate(cls, value):
        """ Negates a boolean value """
        if value in cls.NOT:
            return cls.NOT[value]
        elif value.name == 'True':
            return Value.objects.get(name='False')
        elif value.name == 'False':
            return Value.objects.get(name='True')
        raise NotImplementedError('Negate is only defined for boolean values')


class _BasicMixin(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    snippets = generic.GenericRelation('Snippet')

    class Meta:
        abstract = True

    # These methods allow for convenient access of related traits
    traits = lambda o: o.trait_set.order_by('property__id', 'space__id')
    traits_desc = 'Traits'

    # The following methods are common to Spaces and Properties
    __unicode__ = lambda o: unicode(o.name)
    title = __unicode__

    def save(self, *args, **kwargs):
        """ Automatically slugifies the name if no slug is given """
        if not self.slug:
            self.slug = slugify(self.name)
        # TODO: add valueset default # Ugly hack TODO: set default value_set
        super(_BasicMixin, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return self.__class__.__name__.lower(), (), {'slug': self.slug}

    @models.permalink
    def get_edit_url(self):
        return 'edit_%s' % self.__class__.__name__.lower(), (), {'slug': self.slug}

    @models.permalink
    def get_admin_url(self):
        return 'admin:brubeck_%s_change' % self.__class__.__name__.lower(), (self.id,), {}


class Space(_BasicMixin):
    """ Represents a topological space """
    class Meta:
        app_label = 'brubeck'


class Property(_BasicMixin):
    """ Represents a property like "compact" or "Hausdorff" """
    values = models.ForeignKey('ValueSet', default=ValueSet.BOOLEAN)

    class Meta:
        app_label = 'brubeck'
        verbose_name_plural = 'properties'