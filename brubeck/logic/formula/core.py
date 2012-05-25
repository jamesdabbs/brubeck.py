# Provides tools for working with simple first-order logic type formulae
# describing topological spaces.
from brubeck.models.core import Value, Property


def atomize(property, value):
    """ Replaces (P=True) with P and (P=False) with ~P """
    if value == Value.TRUE or getattr(value, 'name', None) == 'True':
        return '%s' % property
    if value == Value.FALSE or getattr(value, 'name', None) == 'False':
        return '~%s' % property
        # Otherwise, display the full formula
    return '%s = %s' % (property, value)


class Formula(object):
    """ Models a simple logical statement about a topological space. A Formula
        consists of:
        - A statement of the form Property = Value
        - A conjunction (&) of other formulae
        - A disjunction of other formulae
    """
    EQ = '=' # TODO: implement comparisons other than = (for i.e. cardinals)

    AND = '&'
    OR = '|'

    def __init__(self, property=None, value=None, operator=None, sub=None,
                 comparison=EQ):
        """ This constructor builds only atomic formulae. More complicated ones
            can be built by using the & and | operations.

            self.property is always an integer, but if constructed with a
            Property object, it is cached at self._property (sim. Values)
        """
        if isinstance(property, Property):
            self._property = property
            self.property = property.id
        else:
            self.property = property
        if isinstance(value, Value):
            self._value = value
            self.value = value.id
        else:
            self.value = value
        self.comparison = comparison

        if operator and sub:
            self.operator = operator
            self.sub = sub

    def is_atom(self):
        """ Determines whether this formula is atomic (has no subformulae)
        """
        return not hasattr(self, 'sub')

    @classmethod
    def _and_or_or(cls, fst, snd, operator):
        """ Builds a con- or disjunction of subformulae """
        f = Formula(None, None)
        f.operator = operator
        f.sub = []
        for sf in [fst, snd]:
            # Flatten extended conjunctions / disjunctions
            if getattr(sf, 'operator', None) == operator:
                f.sub.extend(sf.sub)
            else:
                f.sub.append(sf)
        return f

    def __and__(self, other):
        """ Joins two formulae together with a logical 'and' """
        return Formula._and_or_or(self, other, Formula.AND)

    def __or__(self, other):
        """ Joins two formulae together with a logical 'or' """
        return Formula._and_or_or(self, other, Formula.OR)

    def __unicode__(self, lookup=False, link=False):
        """ If `lookup` is True, display the Formula using actual Property and
            Value objects (looking them up if needed).

            If `link` is True, each atom will include a link to the Property
            object it references. Note that this always requires a lookup.
        """
        if self.is_atom():
            # Pretty print atomic values
            if lookup: # Use actual Property and Value objects
                self.lookup()
                text = atomize(self._property, self._value)
                return '<a href="%s">%s</a>' % \
                    (self._property.get_absolute_url(), text) if link else text
            else:
                return atomize(self.property, self.value)
        else:
            # Display subformulae recursively
            return u'(%s)' % (u' %s ' % self.operator).join(
                sf.__unicode__(lookup=lookup) for sf in self.sub)

    def __len__(self):
        if hasattr(self, 'sub'):
            return 1 + sum(len(sf) for sf in self.sub)
        return 1

    def negate(self):
        """ Returns a new Formula that is the logical negation of this Formula.
        """
        if self.is_atom():
            return Formula(self.property, Value.negate(self.value))
        else:
            operator = {
                self.AND: self.OR,
                self.OR: self.AND,
                }.get(self.operator, None)
            if operator is None: raise NotImplementedError('Unspecified negation for operator')
            f = Formula(None, None)
            f.operator = operator
            f.sub = [sf.negate() for sf in self.sub]
            return f

    def lookup(self):
        """ Sets self._property and self._value to contain the actual objects
        """
        if self.is_atom():
            if not hasattr(self, '_property'):
                self._property = Property.objects.get(id=self.property)
            if not hasattr(self, '_value'):
                self._value = Value.objects.get(id=self.value)
        else:
            for sf in self.sub:
                sf.lookup()