import json

from django.http import HttpResponse

from brubeck.models import Space, Property, Trait, Implication


class JsonResponse(HttpResponse):
    def __init__(self, val, *args, **kwargs):
        kwargs.update({'mimetype': 'application/json'})
        super(JsonResponse, self).__init__(json.dumps(val), *args, **kwargs)


def _description(obj):
    return obj.snippets.get().revision.text


def spaces(request):
    spaces = [{
        'id': s.id,
        'name': s.name,
        'slug': s.slug,
        'fully_defined': s.fully_defined,
        'description': _description(s)
    } for s in Space.objects.all()]
    return JsonResponse(spaces)


def properties(request):
    properties = [{
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'description': _description(p)
    } for p in Property.objects.all()]
    return JsonResponse(properties)


def traits(request):
    start = request.GET.get('start', 0)
    end = request.GET.get('end', None)
    if end:
        qs = Trait.objects.all()[start:end]
    else:
        qs = Trait.objects.all()[start:]
    traits = [{
        'id': t.id,
        'space_id': t.space_id,
        'property_id': t.property_id,
        'value': t.value.name,
        'description': _description(t),
        'auto': t.snippets[0].automatically_added()
    } for t in qs]
    return JsonResponse(traits)


def get_prep_value(formula):
    if hasattr(formula, 'sub'):
        return '(%s%s)' % (formula.operator,
            ','.join(get_prep_value(sf) for sf in formula.sub))
    p, v = formula.property, formula.value
    p = p.id if hasattr(p, 'id') else p
    v = v.name if hasattr(v, 'name') else v
    return '%s=%s' % (p, v)


def theorems(request):
    theorems = [{
        'id': t.id,
        'antecedent': get_prep_value(t.antecedent),
        'consequent': get_prep_value(t.consequent),
        'description': _description(t)
    } for t in Implication.objects.all()]
    return JsonResponse(theorems)
