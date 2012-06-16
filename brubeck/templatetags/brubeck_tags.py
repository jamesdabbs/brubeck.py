from django import template
from django.db.models.loading import get_model
from django.utils.safestring import mark_safe

import markdown

register = template.Library()


@register.filter
def get(d, k):
    return d.get(k, '')


@register.simple_tag
def contradicts_tag(cx, s, p, t):
    if s == 144:
        return 'class="missing"'

    # Compensate for renumbering
    p = {
        5: 11,
        6: 12,
        7: 13,
        8: 14,
        11: 5,
        12: 6,
        13: 7,
        14: 8,
        34: 35,
        35: 34,
        59: 60,
        60: 61
    }.get(p, p)

    try:
        cxv = cx[s][p]
    except:
        return ''
    if t == '':
        if cxv in ['na', '']:
            return ''
        elif cxv in [0, '0']:
            return 'class="no"'
        else:
            return 'class="yes"'
    # Otherwise t is a trait and we can look up:
    matches = (t.value.name == 'True' and cxv == '1') or \
              (t.value.name == 'False' and cxv == '0') or \
              (t.value.name == 'False' and cxv == 'na')
    if not matches:
        if cxv in ['na', '']:
            return 'class="extra"'
        return 'class="error %s"' % cxv
    return ''


@register.assignment_tag
def lookup_document(doc):
    """ Looks up an object from its corresponding elasticsearch document """
    model = get_model('brubeck', doc['_type'])
    try:
        return model.objects.get(id=doc['_id'])
    except model.DoesNotExist:
        # This may occur if a trait has been deleted but not purged from the
        # index
        from brubeck.search import client
        client.delete(doc['_type'], doc['_id'])


@register.assignment_tag
def get_properties():
    """ Adds the complete list of Properties to the template context. """
    from brubeck.models import Property
    return Property.objects.all()


@register.filter
def columns(l, num):
    """ Splits any sliceable object into `num` sub-objects with (almost)
        equal length.
    """
    length, _columns, num, br = len(l), [], int(num), 0
    q, r = divmod(length, num)
    for i in range(num):
        start = br
        br += q
        if i < r:
            br += 1
        _columns.append(l[start:br])
    return _columns


@register.filter
def smarkdown(text):
    """ Smart markdown of a body of text, preserving MathJAX formatting
    """
    # TODO: Better handling of escaping.
    #       Is this always safe?
    # Prepare the text so that Markdown doesn't remove MathJAX formatting
    text = text.replace('\(', '|(')
    text = text.replace('\)', '|)')

    # Apply markdown, escaping any existing html
    md = markdown.Markdown(safe_mode='escape')
    text = md.convert(text)

    # Re-insert the MathJAX formatting
    text = text.replace('|(', '\(')
    text = text.replace('|)', '\)')
    return mark_safe(text)