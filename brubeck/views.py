import json
from brubeck.search import SearchPaginator

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import paginator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView

from brubeck import forms, utils
from brubeck.logic import Prover
from brubeck.models import Space, Property, Trait, Implication, Revision


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


_get_name = lambda m: m.__name__.lower()


class ModelViewMixin(object):
    def __init__(self, model, *args, **kwargs):
        self.model = model
        self.template_name = 'brubeck/%s/%s.html' % (_get_name(self.__class__),
                                                     _get_name(model))
        super(ModelViewMixin, self).__init__(*args, **kwargs)


class GetObjectMixin(object):
    def get_object(self, queryset=None):
        if self.model == Trait:
            return get_object_or_404(Trait, space__slug=self.kwargs['space'],
                property__slug=self.kwargs['property'])
        elif self.model == Implication:
            return get_object_or_404(Implication, id=self.kwargs['id'])
        return super(GetObjectMixin, self).get_object(queryset)


class List(ModelViewMixin, ListView):
    """ Generates a view for listing one of the core object types """
    paginate_by = 30

    def get_queryset(self):
        return super(List, self).get_queryset().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super(List, self).get_context_data(**kwargs)
        context['plural_name'] = self.model._meta.verbose_name_plural
        context['create_name'] = 'brubeck:create_%s' % \
                                 self.model.__name__.lower()
        return context


def list(request, model):
    return List.as_view(model=model)(request)


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
    start = int(request.GET.get('start', '1'))
    end = int(request.GET.get('end', '144'))
    end = min(end, 143)
    traits = {}
    spaces = Space.defined_objects.filter(id__in=range(start, end + 1))
    for s in spaces:
        traits[s.id] = {}
    properties = Property.objects.all()
    for t in Trait.objects.filter(space__in=spaces):
        traits[t.space.id][t.property.id] = t
    return TemplateResponse(request, 'brubeck/list/table.html', locals())


class Detail(ModelViewMixin, GetObjectMixin, DetailView):
    """ Generates a view for detailing one of the core objects """
    def get_context_data(self, **kwargs):
        context = super(Detail, self).get_context_data(**kwargs)

        # Add paginated list of related traits
        paginator = Paginator(self.object.traits(), 40)
        page = self.request.GET.get('page', 1)
        try:
            traits = paginator.page(page)
        except PageNotAnInteger:
            traits = paginator.page(1)
        except EmptyPage:
            traits = paginator.page(paginator.num_pages)
        context.update({'traits': traits, 'paginator': paginator,
                        'is_paginated': paginator.num_pages > 1})

        # Add reversal information for Implications
        if self.model == Implication:
            cx = self.object.converse().counterexamples()
            if self.request.GET.get('counterexamples', None) != 'all':
                context['reverse_extra'] = max(cx.count() - 3, 0)
                cx = cx[:3]
            context['reverse'] = cx

        # Add unknown space information for Properties
        if self.model == Property:
            spaces = utils.get_unknown_spaces(self.object)
            if self.request.GET.get('unknown', None) != 'all':
                context['unknown_extra'] = max(spaces.count() - 3, 0)
                spaces = spaces[:3]
            context['unknown'] = spaces
        return context


def detail(request, model, **kwargs):
    return Detail.as_view(model=model)(request, **kwargs)


class Revise(ModelViewMixin, GetObjectMixin, DetailView):
    def get_context_data(self, **kwargs):
        context = super(Revise, self).get_context_data(**kwargs)
        context['snippets'] = self.object.snippets.all()

        # Get revision to view, if in GET params
        if 'view' in self.request.GET:
            try:
                r = Revision.objects.get(id=int(self.request.GET['view']))
                assert r.page.snippet in context['snippets']
                context['revision'] = r
            except Exception:
                raise
        return context

    def post(self, request, *args, **kwargs):
        rev = get_object_or_404(Revision,
            id=int(request.POST.get('rev_id', 0)))
        rev.page.revision = rev
        rev.page.save()
        return redirect(rev.page.snippet.object)


@user_passes_test(lambda u: u.is_superuser)
def revision_detail(request, model, **kwargs):
    return Revise.as_view(model=model)(request, **kwargs)


class Create(ModelViewMixin, CreateView):
    """ Generates a view for creating a new core object """
    def get_form_class(self):
        form_class = getattr(forms, '%sForm' % self.model.__name__)
        form_class.user = self.request.user
        return form_class

    def get_form_kwargs(self):
        kwargs = super(Create, self).get_form_kwargs()
        initial = kwargs.get('initial', {})
        initial.update({
            'space': self.request.GET.get('space', ''),
            'property': self.request.GET.get('property', '')
        })
        kwargs['initial'] = initial
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(Create, self).get_context_data(**kwargs)
        context['cls_name'] = _get_name(self.model)
        return context


# TODO: extra permissions handling
def create(request, model):
    return login_required(Create.as_view(model=model))(request)


class Edit(ModelViewMixin, GetObjectMixin, UpdateView):
    """ Generates a view for editing a core object """
    def get_form_class(self):
        form_class = forms.EditForm
        form_class.user = self.request.user
        return form_class

    def get_success_url(self):
        return self.get_object().get_absolute_url()


def edit(request, model, **kwargs):
    return login_required(Edit.as_view(model=model))(request, **kwargs)


def search(request):
    """ Allows a user to search the database """
    # TODO: searching by text may be slow. Should it be AJAXy? Factored into
    #       a separate view?
    # TODO: the template inheritance for the two different column types is
    #       messy. It might be easier to actually use different templates for
    #       the different result types (space only, text only, space & text)
    context = {}
    if 'q' in request.GET:
        form = forms.SearchForm(request.GET)
        if form.is_valid():
            results = form.search()
            # Pre-process the results for the template
            if 'text' in results:
            # Set count
                text_paginator = SearchPaginator(results['text'], 10)
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


class Delete(ModelViewMixin, GetObjectMixin, DetailView):
    # TODO: deal with potential race condition with deleting and re-adding
    model = None
    form_class = forms.DeleteForm

    def get_context_data(self, **kwargs):
        context = super(Delete, self).get_context_data(**kwargs)
        context['orphans'] = utils.get_orphans(self.object)
        return context

    def post(self, *args, **kwargs):
        object = self.get_object()

        if 'confirm' in self.request.POST and self.request.user.is_superuser:
            orphans = utils.get_orphans(object)
            o_count = len(orphans)
            for o in orphans:
                o.delete()
            object.delete()

        old = Trait.objects.count()
        Prover._add_proofs()
        new = Trait.objects.count()
        messages.warning(self.request,
            '%s proof(s) deleted. %s automatically recovered.' %
            (o_count + 1, new - old))
        return redirect('brubeck:home')


@login_required
def delete(request, model, **kwargs):
    # This view is limited to superusers only
    if not request.user.is_superuser:
        raise Http404
    return Delete.as_view(model=model)(request, **kwargs)


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