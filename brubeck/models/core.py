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
        super(_BasicMixin, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return 'brubeck:%s' % self.__class__.__name__.lower(), (), \
            {'slug': self.slug}

    @models.permalink
    def get_edit_url(self):
        return 'brubeck:edit_%s' % self.__class__.__name__.lower(), (), \
            {'slug': self.slug}

    @models.permalink
    def get_revision_url(self):
        return 'brubeck:revise_%s' % self.__class__.__name__.lower(), (), \
            {'slug': self.slug}

    @models.permalink
    def get_admin_url(self):
        return 'admin:brubeck_%s_change' % self.__class__.__name__.lower(), \
            (self.id,), {}

    @property
    def snippets(self):
        # workaround for this bug: http://code.djangoproject.com/ticket/12728
        # replies = generic.GenericRelation(ThreadedComment)
        from django.contrib.contenttypes.models import ContentType
        from brubeck.models.snippets import Snippet
        type = ContentType.objects.get_for_model(self)
        return Snippet.objects.filter(content_type__pk=type.id,
            object_id=self.id)

    @property
    def description(self):
        return self.snippets.get().revision.text


class DefinedManager(models.Manager):
    """ Limits results to Spaces that are fully defined """
    def get_query_set(self):
        return super(DefinedManager, self).get_query_set().filter(
            fully_defined=True)


class Space(_BasicMixin):
    """ Represents a topological space """
    fully_defined = models.BooleanField(default=True)

    # Model managers
    objects = models.Manager()
    defined_objects = DefinedManager()

    class Meta:
        app_label = 'brubeck'


class Property(_BasicMixin):
    """ Represents a property like "compact" or "Hausdorff" """
    values = models.ForeignKey('ValueSet', default=ValueSet.BOOLEAN)

    class Meta:
        app_label = 'brubeck'
        verbose_name_plural = 'properties'

    def allowed_values(self):
        return Value.objects.filter(value_set=self.values)
