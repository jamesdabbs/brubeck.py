from brubeck.logic.formula.utils import human_to_formula
from brubeck.logic.utils import spaces_matching_formula
from django import forms
from django.contrib.auth.forms import UserCreationForm

from brubeck.models import Space, Property, Trait, Implication
from brubeck.utils import add_snippet
from django.core.exceptions import ValidationError


class RegistrationForm(UserCreationForm):
    """ A form for registering new Users w/ site Profiles """
    pass


class SnippetForm(forms.ModelForm):
    """ A ModelForm that also adds a Snippet describing the object it saves
    """
    description = forms.CharField(widget=forms.Textarea())

    def save(self):
        obj = super(SnippetForm, self).save()
        add_snippet(obj, self.cleaned_data['description'], user=self.user)
        return obj


class SpaceForm(SnippetForm):
    """ A simple form for creating and editing a Space """
    class Meta:
        model = Space
        fields = ('name', 'description',)


class PropertyForm(SnippetForm):
    """ A simple form for creating and editing a Property.

        Automatically sets the allowed values to boolean (currently the only
        supported value set).
    """
    class Meta:
        model = Property
        fields = ('name', 'description',)


class TraitForm(SnippetForm):
    """ A form for creating and editing a Trait """
    # TODO: Initialize and validate value based on property.allowed_values
    # TODO: Validate against integrity errors?
    class Meta:
        model = Trait


class ImplicationForm(SnippetForm):
    """ A form for creating and editing an Implication """
    class Meta:
        model = Implication


class SearchForm(forms.Form):
    """ A form for searching the database """
    q = forms.CharField()

    def search(self):
        # TODO: Refactor to search_formula and search_text
        # TODO: More robust text search, ignore \('s \frac{'s, &c.
        q = self.cleaned_data['q']
        try:
            formula = human_to_formula(q)
            res = [(
                'Matching "%s"' % formula.__unicode__(lookup=True),
                Space.objects.filter(id__in=spaces_matching_formula(formula))
            )]
        except ValidationError as e:
            res = [('By formula', e.messages)]
        for cls in [Space, Property, Trait, Implication]:
            res.append(('By %s description' % cls.__name__.lower(),
                cls.objects.filter(snippets__revision__text__icontains=q)))
        return res