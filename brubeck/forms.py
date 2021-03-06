from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from brubeck.logic import Prover
from brubeck.logic.formula.utils import human_to_formula
from brubeck.models import Space, Property, Trait, Implication, Value


class RegistrationForm(UserCreationForm):
    """ A form for registering new Users w/ site Profiles """
    pass


class SnippetForm(forms.ModelForm):
    """ A ModelForm that also adds a Snippet describing the object it saves
    """
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 8}),
        help_text='<em><a href="http://en.wikipedia.org/wiki/Markdown">'
                  'Markdown</a> syntax is supported</em>')


class EditForm(forms.Form):
    """ A form for editing snippets attached to an object (by adding new
        revisions).
    """
    # While it seems natual to subclass SnippetForm, the view logic is cleaner
    # if this ISN'T a ModelFrom.
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 8}),
        help_text='<em><a href="http://en.wikipedia.org/wiki/Markdown">'
                  'Markdown</a> syntax is supported</em>')

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
    # TODO: if given space / property, bind and filter choices (and allow
    #       option to clear binding)
    class Meta:
        model = Trait

    def clean(self):
        """ Verifies that the value selected is valid for the property selected
        """
        cd = super(TraitForm, self).clean()
        value, property = cd.get('value', ''), cd.get('property', '')
        if not (value and property):
            return cd
        try:
            property.allowed_values().get(id=value.id)
            return cd
        except Value.DoesNotExist:
            raise ValidationError('%s is not a valid value for property %s' %
                (value, property))


class ImplicationForm(SnippetForm):
    """ A form for creating and editing an Implication """
    class Meta:
        model = Implication
        fields = ('antecedent', 'consequent')
        widgets = {
            'antecedent': forms.TextInput(
                attrs={'class': 'formula-autocomplete'}),
            'consequent': forms.TextInput(
                attrs={'class': 'formula-autocomplete'}),
        }

    def clean(self):
        """ Checks for existing counterexamples before adding a new implication
        """
        cd = super(ImplicationForm, self).clean()
        ant, cons = cd.get('antecedent', ''), cd.get('consequent', '')
        if not (ant and cons):
            return cd
        cx = Implication(antecedent=ant, consequent=cons).counterexamples()
        if cx.exists():
            raise ValidationError(
                'Cannot save implication. Found counterexample: %s' % cx[0])
        return cd


def _get_start(page_number, per_page):
    try:
        start = (int(page_number) - 1) * per_page
        return 0 if start < 0 else start
    except TypeError:
        return 0


class SearchForm(forms.Form):
    """ A form for searching the database """
    SPACES_PER_PAGE = 25
    TEXTS_PER_PAGE = 10

    q = forms.CharField(required=False,
        widget=forms.TextInput(attrs={'class': 'formula-autocomplete'}))

    def search(self):
        q, res = self.cleaned_data.get('q', '').strip(), {}

        # TODO: unicode support is problematic because of a bug in
        #   urllib. For now, we'll remove accents and hope for the best
        #   Moving forward, we need to completely audit unicode
        #   handling throughout the application.
        import unicodedata
        q = ''.join((c for c in unicodedata.normalize('NFD', q)
            if unicodedata.category(c) != 'Mn'))

        if not q:
            return res

        # Try to parse as a formula
        try:
            f = human_to_formula(q)
            if f.is_empty():
                res['f'], res['f_spaces'] = '', []
            else:
                res['f'] = f.__unicode__(lookup=True, link=True)
                res['f_spaces'] = Space.objects.filter(
                    id__in=Prover.spaces_matching_formula(f))
        except ValidationError as e:
            res['f_errors'] = e.messages

        # Trim trailing separators
        if q and q[-1] in ['+', '|']:
            q = q[:-1].rstrip()
        # Slight optimization: if q contained a '+' or '|' and validated as a
        # formula, it will almost certainly not match any text
        if 'f' in res and ('+' in q or '|' in q):
            return res

        # Otherwise, include the text to search by
        res['text'] = q
        return res


class DeleteForm(forms.Form):
    pass
