from django.core.exceptions import ValidationError

from brubeck.models.core import Property, Value

from .core import Formula


def parse_formula(string):
    """ Converts a string to a Formula, in the inverse of FormulaField's
        to_python method.
    """
    if string[0] == '(':
        # Trim off the first and last parentheses
        string = string[1:-1]

        if '(' in string:
            # TODO: Implement support for nested subformulae
            raise NotImplementedError('Cannot parse nested subformulae')

        f = Formula(None, None)
        f.operator = string[0]
        f.sub = [parse_formula(sf) for sf in string[1:].split(',')]
        return f
    else:
        # This string represents an atom and has the form p=v
        return Formula(*string.split('='))


def _deatomize(a):
    if '=' in a:
        pstr, vstr = a.split('=')
    elif a.startswith('~'):
        pstr, vstr = a[1:], '~'
    elif a.lower().startswith('not '):
        pstr, vstr = a[4:], '~'
    else:
        pstr, vstr = a, '+'
    return pstr, vstr

def _get_value(vstr):
    TRUE = Value.objects.get(name='True')
    FALSE = Value.objects.get(name='False')

    if vstr == '+':
        value = TRUE
    elif vstr in ['~', '-']:
        value = FALSE
    else:
        try:
            value = Value.objects.get(id=int(vstr))
        except ValueError:
            try:
                value = Value.objects.get(name__iexact=vstr)
            except Value.DoesNotExist:
                raise ValidationError('Could not parse value "%s"' % vstr)
    return value

def _get_property(pstr):
    try:
        property = Property.objects.get(id=int(pstr))
    except ValueError:
        try:
            property = Property.objects.get(name__iexact=pstr)
        except Property.DoesNotExist:
            raise ValidationError('Could not parse property "%s"' % pstr)
    return property

def human_to_formula(string):
    """ Takes a string (as would be received from a human-completed form field)
        and attempts to return the formula it represents.
    """
    # TODO: Accents, LaTeX characters, mispellings, aliases (T_2 -> Hausdorff)
    # Trim off trailing whitespace and separators
    string = string.strip()
    if string[-1] in ['+', '|']:
        string = string[:-1].strip()

    # TODO: add multiple operator and subformula support
    if '+' in string and '|' in string:
        raise ValidationError('Could not parse formula. Combined AND and OR is not implemented (yet).')

    if '+' in string:
        separator = '+'
        operator = Formula.AND
    elif '|' in string:
        separator = '|'
        operator = Formula.OR
    else:
        separator = None

    # Iterate over the atoms and look up their formulae
    atoms = string.split(separator) if separator else [string]
    sf = []
    for a in atoms:
        pstr, vstr = _deatomize(a.strip())
        value = _get_value(vstr)
        property = _get_property(pstr)
        sf.append(Formula(property=property, value=value))
    # If AND or OR'ing, build a formula joining the subformulae
    if separator:
        return Formula(operator=operator, sub=sf)
    # Otherwise, there's only one subformula, and it's the whole thing
    else:
        return sf[0]