from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse_lazy
from django.views.generic.base import TemplateView, RedirectView

from brubeck.models import Space, Property, Trait, Implication


urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='brubeck/home.html'),
        name='home'),
)

urlpatterns += patterns('django.contrib.auth.views',
    url('^login/$', 'login',
        {'template_name': 'brubeck/registration/login.html'}, name='login'),
    url('^logout/$', 'logout',
        {'next_page': reverse_lazy('brubeck:home')}, name='logout'),
)

urlpatterns += patterns('brubeck.views',
    # Misc views
    url(r'^browse/$', 'browse', name='browse'),
    url(r'^search/$', 'search', name='search'),
    url(r'^contribute/$', TemplateView.as_view(
        template_name='brubeck/contribute/home.html'), name='contribute'),
    url(r'^contribute/descriptions/$', 'needing_descriptions',
        name='needing_descriptions'),
    url(r'^contribute/counterexamples/$', 'reversal_counterexamples',
        name='needing_counterexamples'),
    url(r'^register/$', 'register', name='register'),
    url(r'^to/github/$', RedirectView.as_view(
        url='https://github.com/jamesdabbs/brubeck'), name='github'),

    # List Views
    url(r'^spaces/$', 'list', {'model': Space}, name='spaces'),
    url(r'^properties/$', 'list', {'model': Property}, name='properties'),
    url(r'^traits/$', 'list', {'model': Trait}, name='traits'),
    url(r'^traits/table/$', 'table', name='table'),
    url(r'^implications/$', 'list',
            {'model': Implication}, name='implications'),

    # Create Views
    url(r'^spaces/create/$', 'create',
        {'model': Space}, name='create_space'),
    url(r'^properties/create/$', 'create',
        {'model': Property}, name='create_property'),
    url(r'^traits/create/$', 'create',
        {'model': Trait}, name='create_trait'),
    url(r'^implications/create/$', 'create',
        {'model': Implication}, name='create_implication'),

    # Edit Views (un-ambiguous locations)
    url(r'^spaces/(?P<slug>[-\w]+)/edit/$', 'edit',
            {'model': Space}, name='edit_space'),
    url(r'^properties/(?P<slug>[-\w]+)/edit/$', 'edit',
            {'model': Property}, name='edit_property'),
    url(r'^implications/(?P<id>\d+)/edit/$', 'edit',
            {'model': Implication}, name='edit_implication'),
    url(r'^(?P<space>[-\w]+)/(?P<property>[-\w]+)/edit/$', 'edit',
            {'model': Trait}, name='edit_trait'),

    # Extra proof tools
    url(r'^(?P<s>[-\w]+)/(?P<p>[-\w]+)/proof/ajax/$', 'proof_ajax',
        name='prove_trait_ajax'),
    url(r'^(?P<s>[-\w]+)/(?P<p>[-\w]+)/proof/$', 'proof', name='prove_trait'),
    url(r'^implications/(?P<id>\d+)/delete/$', 'delete',
            {'model': Implication}, name='delete_implication'),
    url(r'^(?P<space>[-\w]+)/(?P<property>[-\w]+)/delete/$', 'delete',
            {'model': Trait}, name='delete_trait'),

    # Revision control views
    url(r'^spaces/(?P<slug>[-\w]+)/rev/$', 'revision_detail',
            {'model': Space}, name='revise_space'),
    url(r'^properties/(?P<slug>[-\w]+)/rev/$', 'revision_detail',
            {'model': Property}, name='revise_property'),
    url(r'^implications/(?P<id>\d+)/rev/$', 'revision_detail',
            {'model': Implication}, name='revise_implication'),
    url(r'^(?P<space>[-\w]+)/(?P<property>[-\w]+)/rev/$', 'revision_detail',
            {'model': Trait}, name='revise_trait'),

    # Views for redirections coming from old webspace
    url(r'^migrate/([-\w]+)/$', 'migrate'),
    url(r'^migrate/([-\w]+)/([-\w]+)/$', 'migrate'),

    # Detail Views (un-ambiguous locations)
    url(r'^spaces/(?P<slug>[-\w]+)/$', 'detail',
        {'model': Space}, name='space'),
    url(r'^properties/(?P<slug>[-\w]+)/$', 'detail',
        {'model': Property}, name='property'),
    url(r'^(?P<slug>[-\w]+)/$', 'disambiguate', name='disambiguate'),
    url(r'^implications/(?P<id>\d+)/$', 'detail',
            {'model': Implication}, name='implication'),
    url(r'^(?P<space>[-\w]+)/(?P<property>[-\w]+)/$', 'detail',
        {'model': Trait}, name='trait'),

    # Note that the previous urlpattern is fairly greedy and probably ought to
    # remain the last one. Include new urls below here at your own peril.
)
