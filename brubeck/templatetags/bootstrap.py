# Tools for rendering bootstrap-related components
import re

from django import template
from django.template import Node, TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def bootstrap(bound_field, args=''):
    """ Renders a form or form field, wrapping each field in the default
        bootstrap div structure. Takes optional args, including
        - placeholder
    """
    if not bound_field:
        return ''

    # The field may be an entire form. If so, bootstrap all the things.
    if hasattr(bound_field, 'visible_fields'):
        head = render_to_string('brubeck/includes/bootstrap/form_head.html', {
            'form': bound_field})
        body = '\n'.join(
            bootstrap(f, args) for f in bound_field.visible_fields())
        return mark_safe('%s\n%s' % (head, body))

    # Parse out the extra arguments
    args = args.split()
    classes = ''  # a ' '-delimited list of classes
    kwargs = {}  # a dict of extra arguments
    label, inline = True, False
    for arg in args:
        if '=' in arg:
            k, v = arg.split('=')
            kwargs[k] = v
        elif arg == 'no-label':
            label = False
        elif arg == 'inline':
            inline = True
        else:
            classes += ' %s' % arg

    # Changes to the default widget
    if classes:
        attrs = bound_field.field.widget.attrs
        attrs['class'] = '%s%s' % (attrs.get('class', ''), classes)
    if 'placeholder' in kwargs:
        attrs['placeholder'] = kwargs['placeholder']

    return render_to_string("brubeck/includes/bootstrap/field.html", {
        'field': bound_field,
        'required': bound_field.field.required,
        'label': label, 'inline': inline,
    })


@register.simple_tag
def alert(message, cls=''):
    return mark_safe(render_to_string("brubeck/includes/bootstrap/alert.html",
        {'message': message, 'cls': cls}))


kwarg_re = re.compile(r"(?:(.+)=)?(.+)")


# This snippet taken from django_tables2's template tags
def token_kwargs(bits, parser):
    """
    Based on Django's ``django.template.defaulttags.token_kwargs``, but with a
    few changes:

    - No legacy mode.
    - Both keys and values are compiled as a filter
    """
    if not bits:
        return {}
    kwargs = SortedDict()
    while bits:
        match = kwarg_re.match(bits[0])
        if not match or not match.group(1):
            return kwargs
        key, value = match.groups()
        del bits[:1]
        kwargs[parser.compile_filter(key)] = parser.compile_filter(value)
    return kwargs


class QuerystringNode(Node):
    def __init__(self, params):
        super(QuerystringNode, self).__init__()
        self.params = params

    def render(self, context):
        request = context.get('request', None)
        if not request:
            return ""
        params = dict(request.GET)
        for key, value in self.params.iteritems():
            key = key.resolve(context)
            value = value.resolve(context)
            if key not in ("", None):
                params[key] = value
        return escape("?" + urlencode(params, doseq=True))


@register.tag
def querystring(parser, token):
    """
    Creates a URL (containing only the querystring [including "?"]) derived
    from the current URL's querystring, by updating it with the provided
    keyword arguments.

    Example (imagine URL is ``/abc/?gender=male&name=Brad``)::

        {% querystring "name"="Ayers" "age"=20 %}
        ?name=Ayers&gender=male&age=20

    """
    bits = token.split_contents()
    tag = bits.pop(0)
    try:
        return QuerystringNode(token_kwargs(bits, parser))
    finally:
        # ``bits`` should now be empty, if this is not the case, it means there
        # was some junk arguments that token_kwargs couldn't handle.
        if bits:
            raise TemplateSyntaxError("Malformed arguments to '%s'" % tag)


@register.simple_tag
def pagination(page, request, param_name='page'):
    """ Renders a pagination widget using the given page and paginator.
        If given, param_name is the GET argument determining the page number.

        `request` is needed since pagination grabs the current GET params from
        that.
    """
    # TODO: convert this into a non-simple tag that does not require request
    #       to be explicitly given
    return render_to_string('brubeck/includes/bootstrap/pagination.html', {
        'page_obj': page,
        'paginator': page.paginator,
        'request': request,
        'param_name': param_name
    })
