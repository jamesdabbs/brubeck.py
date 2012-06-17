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


def _escape(string, chars):
    for c in chars:
        string = string.replace(c, '\\' + c)
    return string


@register.filter
def smarkdown(text):
    """ Smart markdown of a body of text, preserving MathJAX formatting
    """
    # TODO: this can probably be simplified with some regexes / better escape
    #       handling.
    # TODO: add tests for proper handling and XSS tests
    # TODO: \( \{(x,y) | |(x,y)| < 1\} \) errors b/c of replacements
    text = text.replace('\(', '|(').replace('\)', '|)').replace(
                        '\[', '|[').replace('\]', '|]')

    res, store, delimiter, out = [], '', None, True
    for i in range(len(text)):
        # Check if we're moving into a parenthetical grouping
        if text[i:].startswith('|('):
            res.append(store)
            store, delimiter, out = '', '|)', False
        elif text[i:].startswith('|['):
            res.append(store)
            store, delimiter, out = '', '|]', False
        # Check if we're moving out of a parenthetical grouping
        elif not out and delimiter and text[i:].startswith(delimiter):
            # Don't escape the delimeter (which has length 2), but do escape
            # other Markdown formatting characters
            res.append(store[:2] + _escape(store[2:], '\\`*_{}[]()#+-.!'))
            store, delimiter = '', None
        store += text[i]
    # Append the last store / delimiter
    res.append(store)

    md = markdown.Markdown(safe_mode='escape')
    text = md.convert(''.join(res))
    return mark_safe(text.replace('|(', '\(').replace('|)', '\)').replace(
                                  '|[', '\[').replace('|]', '\]'))
