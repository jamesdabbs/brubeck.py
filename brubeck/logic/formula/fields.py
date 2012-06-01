from django import forms
from django.db import models

from . import utils
from .core import Formula


class FormulaField(models.CharField):
    """ Allows models to conveniently use Formulae as attributes

        Formulae are stored in the database as specified by th
        - <property_id>=<value_id> for atomic formulae
        - (f1|f2|...|fn) for disjunctions of n subformulae (sim. &)
    """
    description = 'A first-order statement about the properties of a space'

    # This metaclass ensures that to_python will be called
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        """ Sets the max_length to a roomy enough default """
        kwargs['max_length'] = 1024
        super(FormulaField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, Formula):  # No conversion necessary
            return value

        if not value:
            return Formula()

        return utils.parse_formula(value)

    def get_prep_value(self, value):
        if hasattr(value, 'sub'):
            return '(%s%s)' % (value.operator,
                ','.join(self.get_prep_value(sf) for sf in value.sub))
        p, v = value.property, value.value
        p = p.id if hasattr(p, 'id') else p
        v = v.id if hasattr(v, 'id') else v
        return '%s=%s' % (p, v)

    def value_to_string(self, obj):
        """ Converts this object to a string to be serialized """
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)

    # TODO: Make sense of queries like "property=compact" (to get all traits
    # or implications involving compactness) or "property=compact, value=True"
    # (to get all traits saying a space is compact)

    def formfield(self, **kwargs):
        defaults = {'form_class': FormulaCharField}
        defaults.update(kwargs)
        return super(FormulaField, self).formfield(**defaults)


class FormulaCharField(forms.CharField):
    def clean(self, value):
        return utils.human_to_formula(value)
