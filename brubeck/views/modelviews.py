from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from brubeck import utils, forms
from brubeck.logic import Prover
from brubeck.models import Space, Property, Trait, Implication, Snippet,\
    Revision

_get_name = lambda m: m.__name__.lower()


class ModelViewMixin(object):
    def __init__(self, model, *args, **kwargs):
        self.model = model
        self.template_name = 'brubeck/%s/%s.html' % (_get_name(self.__class__),
                                                     _get_name(model))
        super(ModelViewMixin, self).__init__(*args, **kwargs)


class GetObjectMixin(ModelViewMixin):
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
        context['create_name'] = 'brubeck:create_%s' %\
                                 self.model.__name__.lower()
        return context


def list(request, model):
    return List.as_view(model=model)(request)


class Detail(GetObjectMixin, DetailView):
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

        # Add "traits needing descriptions" for Spaces or Properties
        if self.model in [Space, Property]:
            context['traits_needing_descriptions'] =\
            utils.traits_needing_descriptions(self.object)
        return context


def detail(request, model, **kwargs):
    return Detail.as_view(model=model)(request, **kwargs)


class Revise(GetObjectMixin, DetailView):
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

    def form_valid(self, form):
        obj = form.save()
        snippet = Snippet.objects.create(object=obj)
        snippet.add_revision(user=self.request.user,
            text=form.cleaned_data['description'])
        return redirect(obj)


# TODO: extra permissions handling
def create(request, model):
    return login_required(Create.as_view(model=model))(request)


class Edit(GetObjectMixin, UpdateView):
    """ Generates a view for editing a core object """
    def get_form_class(self):
        form_class = forms.EditForm
        form_class.user = self.request.user
        return form_class

    def get_success_url(self):
        return self.get_object().get_absolute_url()


def edit(request, model, **kwargs):
    return login_required(Edit.as_view(model=model))(request, **kwargs)


class Delete(GetObjectMixin, DetailView):
    # TODO: deal with potential race condition with deleting and re-adding
    model = None
    form_class = forms.DeleteForm

    def get_context_data(self, **kwargs):
        context = super(Delete, self).get_context_data(**kwargs)
        context['orphans'] = utils.get_orphans(self.object)
        return context

    def post(self, *args, **kwargs):
        object = self.get_object()

        o_count = 0
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


@user_passes_test(lambda u: u.is_superuser)
def delete(request, model, **kwargs):
    return Delete.as_view(model=model)(request, **kwargs)
