try:
    # South needs to know how to freeze custom model fields
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^brubeck\.logic\.formula\.fields\.FormulaField"])
    add_introspection_rules([], ["^brubeck\.fields\.SetField"])
except ImportError:
    # We'll assume South isn't installed and not worry about it
    pass

from .core import *
from .provable import *
from .wiki import *
from .snippets import *
from .profile import *