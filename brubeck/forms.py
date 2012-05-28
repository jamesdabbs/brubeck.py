from brubeck.models.core import Value
from django import forms
from django.contrib.auth.forms import UserCreationForm

from brubeck.logic.formula.utils import human_to_formula
from brubeck.logic.utils import spaces_matching_formula
from brubeck.models import Space, Property, Trait, Implication
from brubeck import utils
from django.core.exceptions import ValidationError


class RegistrationForm(UserCreationForm):
    """ A form for registering new Users w/ site Profiles """
    pass


class SnippetForm(forms.ModelForm):
    """ A ModelForm that also adds a Snippet describing the object it saves
    """
    description = forms.CharField(widget=forms.Textarea())

    def save(self, commit=True, add_snippet=True):
        # TODO: check. Changed so implication's clean could work
        obj = super(SnippetForm, self).save(commit=commit)
        if add_snippet:
            utils.add_snippet(obj, self.cleaned_data['description'], user=self.user)
        return obj


class EditForm(forms.Form):
    """ A form for editing snippets attached to an object (by adding new
        revisions).
    """
    description = forms.CharField(widget=forms.Textarea())

    def _get_snippet(self, obj):
        return obj.snippets.all()[0]

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance')
        kwargs['initial'].update({
            'description': self._get_snippet(instance).revision.text
        })
        super(EditForm, self).__init__(*args, **kwargs)
        self.instance = instance

    def save(self, *args, **kwargs):
        self._get_snippet(self.instance).add_revision(
            text=self.cleaned_data['description'],
            user=self.user
        )

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
    class Meta:
        model = Trait

    def clean(self):
        """ Verifies that the value selected is valid for the property selected
        """
        cd = super(TraitForm, self).clean()
        value, property = cd.get('value', ''), cd.get('property', '')
        if not (value and property): return cd
        try:
            property.allowed_values().get(id=value.id)
            return cd
        except Value.DoesNotExist:
            raise ValidationError('%s is not a valid value for property %s' %\
                (value, property))


class ImplicationForm(SnippetForm):
    """ A form for creating and editing an Implication """
    class Meta:
        model = Implication
        fields = ('antecedent', 'consequent')

    def clean(self):
        """ Checks for existing counterexamples before adding a new implication
        """
        cd = super(ImplicationForm, self).clean()
        ant, cons= cd.get('antecedent', ''), cd.get('consequent', '')
        if not (ant and cons): return cd
        cx = Implication(antecedent=ant, consequent=cons).counterexamples()
        if cx.exists():
            raise ValidationError(
                'Cannot save implication. Found counterexample: %s' % cx[0])
        return cd


class SearchForm(forms.Form):
    """ A form for searching the database """
    q = forms.CharField()

    def search(self):
        # TODO: Refactor to search_formula and search_text
        # TODO: More robust text search, ignore \('s \frac{'s, &c.
        # TODO: e.g. `compact` should show implications involving compactness
        q = self.cleaned_data['q']
        # Trim off a trailing ' + '
        q = q.strip()
        if q[-1] == '+':
            q = q[:-1].strip()
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


class DeleteForm(forms.Form):
    pass