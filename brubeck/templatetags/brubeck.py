from django import template

register = template.Library()


@register.filter
def get(d, k):
    return d.get(k, '')


@register.simple_tag
def contradicts_tag(cx, s, p, t):
    if s == 144: return 'class="missing"'

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