# Tests the core brubeck views
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from brubeck.logic.formula.utils import human_to_formula
from brubeck.models import Space, Property, Trait, Implication, Value, \
    Profile, Revision


class RegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup(self):
        url = reverse('brubeck:register')
        # Test getting
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Test registering
        response = self.client.post(url, {
            'username': 'user',
            'password1': 'pass',
            'password2': 'pass',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Profile.objects.count(), 1)


class DisambiguationTest(TestCase):
    """ Tests that the slug disambiguation view works. Note that (by necessity)
        ambiguous urls won't be produced by reversing, so this test assumes
        that brubeck urls are set up under '/brubeck/'
    """
    def setUp(self):
        self.client = Client()
        self.a = Space.objects.create(name='a', slug='a')
        self.b = Space.objects.create(name='b', slug='b')
        Property.objects.create(name='a', slug='a')
        self.c = Property.objects.create(name='c', slug='c')

    def test_single_objects(self):
        """ Tests that the single objects' slugs redirect to the objects """
        response = self.client.get('/brubeck/%s/' % self.b.slug)
        self.assertRedirects(response, self.b.get_absolute_url())
        response = self.client.get('/brubeck/%s/' % self.c.slug)
        self.assertRedirects(response, self.c.get_absolute_url())

    def test_non_existent(self):
        """ Tests that disambiguation 404's when nothing is found """
        response = self.client.get('/brubeck/non-existent-slug/')
        self.assertEqual(response.status_code, 404)

    def test_disambiguation(self):
        """ Tests that collisions render the disambiguation page """
        response = self.client.get('/brubeck/%s/' % self.a.slug)
        self.assertTemplateUsed(response, 'brubeck/disambiguation.html')


class ProofTest(TestCase):
    fixtures = ['values.json']

    def setUp(self):
        self.client = Client()
        self.space = Space.objects.create(name='Space')
        self.A = Property.objects.create(name='A')
        self.B = Property.objects.create(name='B')
        self.T = Value.objects.get(name='True')
        self.F = Value.objects.get(name='False')
        Implication.objects.create(
            antecedent=human_to_formula('~A'),
            consequent=human_to_formula('B')
        )
        Trait.objects.create(space=self.space, property=self.A, value=self.F)

    def test_get(self):
        """ Tests the initial page load to get the proof page """
        t = Trait.objects.get(space=self.space, property=self.B)
        response = self.client.get(t.get_proof_url())
        self.assertTemplateUsed('brubeck/detail/proof.html')
        assert response.context['object'] == t

    def test_ajax_callback(self):
        """ Tests the ajax callback to get a JSON dump of the proof """
        t = Trait.objects.get(space=self.space, property=self.B)
        url = reverse('brubeck:prove_trait_ajax',
            kwargs={'s': t.space.slug, 'p': t.property.slug})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json = response.content
        assert 'id' in json
        assert 'name' in json


class CRUDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User(username='user')
        self.user.set_password('pass')
        self.user.save()

    def test_create_and_edit_space(self):
        # CREATE
        url = reverse('brubeck:create_space')

        # Test get
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.client.login(username='user', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Test post
        response = self.client.post(url, {
            'name': 'Space',
            'description': 'Space description'
        })
        self.assertEqual(Space.objects.count(), 1)
        space = Space.objects.get()
        self.assertRedirects(response, space.get_absolute_url())

        # Also check that a snippet is created
        revision = Revision.objects.get(text='Space description')
        self.assertEqual(revision.page.snippet.object, space)

        # EDIT
        url = space.get_edit_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Post
        response = self.client.post(url, {
            'description': 'Updated description'
        })
        self.assertRedirects(response, space.get_absolute_url())
        self.assertEqual(Revision.objects.count(), 2)
        self.assertEqual(space.snippets.all()[0].current_text(),
            'Updated description')

        # SET REVISION
        url = space.get_revision_url()
        response = self.client.get(url)
        self.assertRedirects(response, '%s?next=%s' % (
            reverse('brubeck:login'), url))
        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Post
        response = self.client.post(url, {'rev_id': 1})
        self.assertRedirects(response, space.get_absolute_url())
        self.assertEqual(space.snippets.all()[0].revision.id, 1)


#class SitemapTest(TestCase):
#    """ Tests sitemap configuration """
#    fixtures = ['values.json']
#
#    def setUp(self):
#        s = Space.objects.create(name='space')
#        p = Property.objects.create(name='property')
#        Trait.objects.create(space=s, property=p, value=Value.objects.all()[0])
#
#    def test_sitemap(self):
#        from django.contrib.sitemaps.views import sitemap
#        from django.http import HttpRequest
#
#        from brubeck.sitemaps import sitemap as brubeck_sitemap
#
#        sitemap(HttpRequest(), brubeck_sitemap)


#class SearchViewTest(TestCase):
#    """ Tests the search view """
#    # Given that the tests will be querying the live search index, there's only
#    # so much we can test here. This just makes sure that the different types
#    # of queries don't cause any errors.
#    fixtures = ['values.json']
#
#    def setUp(self):
#        self.client = Client()
#        self.url = reverse('brubeck:search')
#        Property.objects.create(name='compact')
#        Property.objects.create(name='connected')
#
#    def test_get(self):
#        response = self.client.get(self.url)
#        self.assertTemplateUsed(response, 'brubeck/search/search.html')
#
#    def test_empty_q(self):
#        response = self.client.get(self.url, {'q': ''})
#        self.assertTemplateUsed(response, 'brubeck/search/search.html')
#
#    def test_formula(self):
#        response = self.client.get(self.url, {'q': 'compact'})
#        self.assertTemplateUsed(response, 'brubeck/search/search.html')
#
#    def test_text(self):
#        response = self.client.get(self.url, {'q': 'lemma'})
#        self.assertTemplateUsed(response, 'brubeck/search/search.html')
#
#    def test_both(self):
#        response = self.client.get(self.url, {'q': 'compact + connected'})
#        self.assertTemplateUsed(response, 'brubeck/search/search.html')
