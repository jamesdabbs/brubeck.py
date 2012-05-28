from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from brubeck import utils
from brubeck.logic.formula.utils import human_to_formula
from brubeck.logic.utils import spaces_matching_formula
from brubeck.models import Space, Property, Trait, Implication, Value


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
        widgets = {
            'antecedent': forms.TextInput(attrs={'class': 'formula-autocomplete'}),
            'consequent': forms.TextInput(attrs={'class': 'formula-autocomplete'}),
        }

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
    q = forms.CharField(required=False,
        widget=forms.TextInput(attrs={'class': 'formula-autocomplete'}))

    def search(self):
        # TODO: More robust text search, ignore \('s \frac{'s, &c.
        # TODO: e.g. `compact` should show implications involving compactness
        q, res = self.cleaned_data.get('q', '').strip(), {}
        if not q: return res

        # Try to parse as a formula
        try:
            f = human_to_formula(q)
            if f.is_empty():
                res['f'], res['f_spaces'] = '', []
            else:
                res['f'] = f.__unicode__(lookup=True, link=True)
                res['f_spaces'] = Space.objects.filter(
                    id__in=spaces_matching_formula(f))
        except Exception as e:
            res['f_errors'] = e.messages

        # Trim trailing separators
        if q and q[-1] in ['+', '|']: q = q[:-1].rstrip()
        # Slight optimization: if q contained a '+' or '|' and validated as a
        # formula, it will almost certainly not match any text
        if 'f' in res and ('+' in q or '|' in q):
            return res

        # Otherwise, we'll also search by text
        from brubeck.search import client

        r = client.search('name:%s OR text:%s' % (q, q))
        res['t_hits'] = r['hits']['hits']
        res['t_count'] = r['hits']['total']
        return res

class DeleteForm(forms.Form):
    pass