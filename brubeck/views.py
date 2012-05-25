from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.generic import ListView, DetailView
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import CreateView, FormView

from brubeck import forms, utils
from brubeck.models import Space, Property, Trait, Implication


def _force_login(request, user):
    """ Hack to log in a newly created user without re-authenticating """
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)


class RegistrationView(FormView):
    form_class = forms.RegistrationForm
    template_name = 'brubeck/registration/register.html'

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, 'Your account has been created')
        _force_login(self.request, user)
        return redirect(self.request.GET.get('next', reverse('home')))

register = RegistrationView.as_view()


_get_name = lambda m: m.__name__.lower()

class ModelViewMixin(object):
    def __init__(self, model, *args, **kwargs):
        self.model = model
        self.template_name = 'brubeck/%s/%s.html' % (_get_name(self.__class__),
                                                     _get_name(model))
        super(ModelViewMixin, self).__init__(*args, **kwargs)


class List(ModelViewMixin, ListView):
    """ Generates a view for listing one of the core object types """
    paginate_by = 30
    
    def get_context_data(self,  **kwargs):
        context = super(List, self).get_context_data(**kwargs)
        context['plural_name'] = self.model._meta.verbose_name_plural
        return context

def list(request, model):
    return List.as_view(model=model)(request)


def table(request):
    """ Prepares a table of all available traits """
    # This page is *very* slow to load. Only display it for superusers.
    if not request.user.is_superuser:
        raise Http404

    # Get the table from counterexamples to compare to
    import csv
    import os

    path = os.path.dirname(os.path.realpath(__file__))
    reader = csv.reader(open(os.path.join(path, 'counterexamples.csv'), 'r'))
    cx = [row for row in reader]

    # And a list of all current traits
    traits = {}
    spaces = Space.objects.all()
    for s in spaces:
        traits[s.id] = {}
    properties = Property.objects.all()
    for t in Trait.objects.all():
        traits[t.space.id][t.property.id] = t
    return TemplateResponse(request, 'brubeck/list/table.html', locals())


class Detail(ModelViewMixin, DetailView):
    """ Generates a view for detailing one of the core objects """
    def get_object(self, queryset=None):
        if self.model == Trait:
            return get_object_or_404(Trait, space__slug=self.kwargs['space'],
                property__slug=self.kwargs['property'])
        elif self.model == Implication:
            return get_object_or_404(Implication, id=self.kwargs['id'])
        return super(Detail, self).get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super(Detail, self).get_context_data(**kwargs)

        # Add paginated list of related traits
        paginator = Paginator(self.object.traits(), 25)
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
            context['reverse'] = self.object.converse().counterexamples()
        return context

def detail(request, model, **kwargs):
    return Detail.as_view(model=model)(request, **kwargs)


class Create(ModelViewMixin, CreateView):
    """ Generates a view for creating a new core object """
    def get_form_class(self):
        form_class = getattr(forms, '%sForm' % self.model.__name__)
        form_class.user = self.request.user
        return form_class

# TODO: extra permissions handling
def create(request, model):
    return login_required(Create.as_view(model=model))(request)


def search(request):
    """ Allows a user to search the database """
    # TODO: implement more robust text search
    # TODO: improve human elements (parsing, suggestions, autocomplete)
    if 'q' in request.GET:
        form = forms.SearchForm(request.GET)
        if form.is_valid():
            results = form.search()
    else:
        form = forms.SearchForm()
    return TemplateResponse(request, 'brubeck/search.html', locals())


contribute = TemplateView.as_view(
    template_name='brubeck/contribute/home.html')

redirect_to_github = RedirectView.as_view(
    url='https://github.com/jamesdabbs/brubeck/')

needing_descriptions = ListView.as_view(
    paginate_by = 30,
    queryset = utils.get_incomplete_snippets().order_by('content_type'),
    template_name = 'brubeck/contribute/descriptions.html')

reversal_counterexamples = ListView.as_view(
    paginate_by = 30,
    queryset = utils.get_open_converses(),
    template_name = 'brubeck/contribute/counterexamples.html')
