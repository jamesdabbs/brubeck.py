# Defines a Cardinal object
# TODO: unicode literals, replace w with \omega

# The string we will use internally to represent \omega
OMEGA = 'w'

def _cast(i):
    # Pass through special values
    if i is None:
        return None
    elif isinstance(i, Cardinal):
        return i
    elif isinstance(i, int):
        if i < 0:
            raise TypeError('Cannot cast negative integers to Cardinals')
        return Cardinal(base=i)
    else:
        raise TypeError('Cannot cast %s to Cardinal' % type(i))

class Cardinal(object):
    """ Models a cardinal, and enables several common operations - most
        most importantly, comparison of cardinals.
    """
    # We only consider cardinals of the following forms:
    # n, for n an integer
    # omega, the first infinite cardinal
    # a_b, for a,b cardinals
    # a^b, for a,b cardinals
    def __init__(self, base, sub=None, exp=None):
        # While similar to _cast, using it directly here causes an infinite
        # recursion.
        if isinstance(base, Cardinal) or base == OMEGA:
            self.base = base
        elif isinstance(base, int):
            if base < 0:
                raise TypeError('Cannot cast negative integers to Cardinals')
            self.base = base
        else:
            raise TypeError('Invalid type for base: %s' % type(base))
        self.sub, self.exp = map(_cast, [sub, exp])

    def is_simple(self):
        return not (self.sub or self.exp)

    # Representation methods
    def __unicode__(self):
        u = unicode(self.base)
        tail = None
        if self.sub:
            u += '_'
            tail = self.sub
        elif self.exp:
            u += '^'
            tail = self.exp
        if tail:
            template = '%s' if tail.is_simple() else '(%s)'
            u += template % tail
        return u

    def __repr__(self):
        return unicode(self)

    # Construction methods - for building new Cardinals from old ones
    def __floordiv__(self, other):
        """ a // b represents a_b """
        if self.sub or self.exp or self.base != OMEGA:
            raise TypeError('Can only subscript %s' % OMEGA)
        if isinstance(other, int):
            other = Cardinal(other)
        return Cardinal(base=self, sub=other)

    def __pow__(self, power, modulo=None):
        """ a ** b represents a^b """
        if modulo:
            raise TypeError('Modular exponentiation is not defined for '
                            'Cardinals')
        return Cardinal(base=self, exp=_cast(power))

    def __rpow__(self, power, modulo=None):
        """ Extends __pow__ to cover the case where a is a integer """
        if modulo:
            raise TypeError('Modular exponentiation is not defined for '
                            'Cardinals')
        return Cardinal(base=_cast(power), exp=self)

    # Comparison methods
    def is_infinite(self):
        return self.base == OMEGA or (self.exp and self.exp.is_infinite())

    def is_finite(self):
        return not self.is_infinite()

    def __lt__(self, other):
        if self.is_infinite():
            pass
            # TODO: flesh out logic and add __gt__, __eq__, reverse methods
        else:  # `self` is finite
            if other.is_infinite():
                return False
            else:
                return self.base < other.base
