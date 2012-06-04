# Defines Sitemaps which can be used to construct a sitemap.xml file
# TODO: Split into sitemap index. Set changefreq, etc.
from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse

from brubeck.models import Space, Property, Trait, Implication


class SpaceSitemap(Sitemap):
    def items(self):
        return Space.objects.all()


class PropertySitemap(Sitemap):
    def items(self):
        return Property.objects.all()


class TraitSitemap(Sitemap):
    def items(self):
        return Trait.objects.all()


class ImplicationSitemap(Sitemap):
    def items(self):
        return Implication.objects.all()


class _EditMixin(object):
    def location(self, object):
        return object.get_edit_url()


class EditSpaceSitemap(SpaceSitemap, _EditMixin):
    pass


class EditPropertySitemap(PropertySitemap, _EditMixin):
    pass


class EditTraitSitemap(TraitSitemap, _EditMixin):
    pass


class EditImplicationSitemap(ImplicationSitemap, _EditMixin):
    pass


class TraitProofSitemap(TraitSitemap):
    def location(self, obj):
        return object.get_proof_url()


class ViewSitemap(Sitemap):
    """Reverse static views for XML sitemap."""
    def items(self):
        # Return list of url names for views to include in sitemap
        return ['home', 'create_space', 'create_property', 'create_trait',
                'create_implication', 'search', 'contribute',
                'needing_descriptions', 'needing_counterexamples']

    def location(self, item):
        return reverse('brubeck:%s' % item)


sitemap = {
    'space': SpaceSitemap,
    'edit_space': EditSpaceSitemap,
    'property': PropertySitemap,
    'edit_property': EditPropertySitemap,
    'trait': TraitSitemap,
    'edit_trait': EditTraitSitemap,
    'implication': ImplicationSitemap,
    'edit_implication': EditImplicationSitemap,
    'static': ViewSitemap
}