# Tools for rendering bootstrap-related components
from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def bootstrap(bound_field, args=''):
    """ Renders a form or form field, wrapping each field in the default
        bootstrap div structure. Takes optional args, including
        - placeholder
    """
    if not bound_field: return ''

    # The field may be an entire form. If so, bootstrap all the things.
    if hasattr(bound_field, 'visible_fields'):
        head = render_to_string('brubeck/includes/bootstrap/form_head.html', {
            'form': bound_field})
        body = '\n'.join(
            bootstrap(f, args) for f in bound_field.visible_fields())
        return mark_safe('%s\n%s' % (head, body))

    # Parse out the extra arguments
    args = args.split()
    classes = '' # a ' '-delimited list of classes
    kwargs = {} # a dict of extra arguments
    label = True
    for arg in args:
        if '=' in arg:
            k,v = arg.split('=')
            kwargs[k] = v
        elif arg == 'no-label':
            label = False
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
        'label': label
    })


@register.simple_tag
def alert(message, cls=''):
    return mark_safe(render_to_string("brubeck/includes/bootstrap/alert.html",
        {'message': message, 'cls': cls}))