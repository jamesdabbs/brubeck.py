from django.db import models


class SetField(models.CharField):
    """ Stores a set of integers in the database as a |-separated string """
    # We store integers in the database surrounded by |'s, so that looking up
    # 1 actually looks up |1| and doesn't match everything with 1 as a digit
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs.update({'default': '||'})
        super(SetField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return
        if isinstance(value, set):
            return value
        return set(int(a) for a in value.split('|') if a)

    def get_prep_value(self, value):
        if not value:
            return '||'
        return '|%s|' % '|'.join(str(a) for a in value)

    def get_prep_lookup(self, lookup_type, value):
        if lookup_type == 'contains':
            return value
        else:
            raise TypeError('Lookup type not supported: %s' % lookup_type)
