import json

from django.contrib import messages
from django.contrib.auth import login
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.decorators.cache import cache_page
from django.views.generic import ListView
from django.views.generic.edit import FormView

from brubeck import forms, utils
from brubeck.logic import Prover
from brubeck.models import Space, Property, Trait, Implication, Profile, \
    Snippet


def _force_login(request, user):
    """ Hack to log in a newly created user without re-authenticating """
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)


# TODO: registration should never redirect you back to login
class RegistrationView(FormView):
    form_class = forms.RegistrationForm
    template_name = 'brubeck/registration/register.html'

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, 'Your account has been created')
        _force_login(self.request, user)
        return redirect(self.request.GET.get('next', reverse('brubeck:home')))
register = RegistrationView.as_view()


def table(request):
    """ Prepares a table of all available traits """
    # This page is *very* slow to load. Only display it for superusers.
    if not request.user.is_superuser:
        raise Http404

    # Get the table from counterexamples to compare to
    import urllib2
    f = urllib2.urlopen(
        'https://s3.amazonaws.com/jdabbs.com/counterexamples.csv').read()
    cx = [row.split(',') for row in f.split('\n')]

    # And a list of all current traits
    try:
        start = int(request.GET['start'])
    except Exception:
        start = 1
    try:
        end = int(request.GET['end'])
    except Exception:
        end = 143
    end = min(end, 143)
    traits = {}
    spaces = Space.defined_objects.filter(id__in=range(start, end + 1))
    for s in spaces:
        traits[s.id] = {}
    properties = Property.objects.all()
    for t in Trait.objects.filter(space__in=spaces):
        traits[t.space.id][t.property.id] = t
    return TemplateResponse(request, 'brubeck/list/table.html', locals())


def search(request):
    """ Allows a user to search the database """
    # TODO: searching by text may be slow. Should it be AJAXy? Factored into
    #       a separate view?
    # TODO: the template inheritance for the two different column types is
    #       messy. It might be easier to actually use different templates for
    #       the different result types (space only, text only, space & text)
    # TODO: Improve and test search.
    context = {}
    if 'q' in request.GET:
        form = forms.SearchForm(request.GET)
        if form.is_valid():
            results = form.search()
            # Pre-process the results for the template
            if 'text' in results:
                text_paginator = Paginator(Snippet.objects.filter(
                    Q(revision__text__icontains=results['text']) |
                    Q(title=results['text'])
                ), 10)
                text_page = request.GET.get('text_page', 1)
                try:
                    text_page = text_paginator.page(text_page)
                except PageNotAnInteger:
                    text_page = text_paginator.page(1)
                except EmptyPage:
                    text_page = text_paginator.page(text_paginator.num_pages)
                context.update({
                    'text_page': text_page,
                    'text_paginator': text_paginator
                })

            formula_paginator = Paginator(results.get('f_spaces', []), 25)
            formula_page = request.GET.get('formula_page', 1)
            try:
                formula_page = formula_paginator.page(formula_page)
            except PageNotAnInteger:
                formula_page = formula_paginator.page(1)
            except EmptyPage:
                formula_page = formula_paginator.page(
                    formula_paginator.num_pages)
            if 'f' in results:
                context.update({
                    'formula': results['f'],
                    'formula_page': formula_page,
                    'formula_paginator': formula_paginator,
                })
            else:
                context['formula_error'] = results.get('f_errors', [''])[0]
    else:
        form = forms.SearchForm()
    context.update({'form': form})
    return TemplateResponse(request, 'brubeck/search/search.html', context)


needing_descriptions = ListView.as_view(
    paginate_by=42,
    queryset=utils.get_incomplete_snippets().order_by('content_type'),
    template_name='brubeck/contribute/descriptions.html')

reversal_counterexamples = ListView.as_view(
    paginate_by=42,
    queryset=utils.get_open_converses(),
    template_name='brubeck/contribute/counterexamples.html')


def proof(request, s, p):
    object = get_object_or_404(Trait, space__slug=s, property__slug=p)
    return TemplateResponse(request, 'brubeck/detail/proof.html', locals())


@cache_page(60 * 60 * 24)
def proof_ajax(request, s, p):
    # if not request.is_ajax(): raise Http404
    trait = get_object_or_404(Trait, space__slug=s, property__slug=p)
    proof = Prover.get_full_proof(trait)
    return HttpResponse(json.dumps(proof),
        content_type='application/json')


def browse(request):
    """ Renders an introductory browse template, with recent items of the
        various types
    """
    LIMIT = 5
    return TemplateResponse(request, 'brubeck/browse.html', {
        'spaces': Space.objects.order_by('-id')[:LIMIT],
        'properties': Property.objects.order_by('-id')[:LIMIT],
        'traits': Trait.objects.order_by('-id')[:LIMIT],
        'implications': Implication.objects.order_by('-id')[:LIMIT]
    })


def profile(request, username):
    """ Displays a user's profile
    """
    profile = get_object_or_404(Profile, user__username=username)

    class _Inner(ListView):
        paginate_by = 5
        queryset = profile.user.revision_set.order_by('-id')
        template_name = 'brubeck/registration/profile.html'

        def get_context_data(self, **kwargs):
            context = super(_Inner, self).get_context_data(**kwargs)
            context.update({
                'profile': profile,
                'is_owner': request.user == profile.user
            })
            return context
    return _Inner.as_view()(request)


profiles = ListView.as_view(
    paginate_by=20,
    queryset=Profile.objects.all(),
    template_name='brubeck/registration/profiles.html'
)


def disambiguate(request, slug):
    """ Given a possibly (but probably not) ambiguous slug, redirects if
        possible, or displays a disambiguation page if not.
    """
    space = Space.objects.filter(slug=slug)
    property = Property.objects.filter(slug=slug)

    if space.exists() and property.exists():
        return TemplateResponse(request, 'brubeck/disambiguation.html', {
            'space': space[0],
            'property': property[0],
            'slug': slug
        })
    if space.exists():
        return redirect(space[0])
    if property.exists():
        return redirect(property[0])
    raise Http404


def migrate(request, *args):
    """ Utility view for pointing database traffic to its new location. This
        should not be needed for other installations.
    """
    try:
        top = args[0].lower()
        if top == 'browse':
            return redirect('brubeck:home', permanent=True)
        if top == 'search':
            return redirect('brubeck:search', permanent=True)
        if len(args) == 1:
            return redirect('brubeck:disambiguate', slug=top, permanent=True)
        if top == 'theorem':
            return redirect('brubeck:implication', id=args[1], permanent=True)
        return redirect('brubeck:trait', space=top, property=args[1].lower(),
            permanent=True)
    except Exception:
        raise Http404
