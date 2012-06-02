# Tests basic brubeck url reversals and simple views
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from brubeck.models import Space, Property, Trait, Implication, Value, ValueSet


class SmokeTests(TestCase):
    """ These tests should be simple url lookup / page loads, but should help
        catch any glaring configuration errors.
    """
    fixtures = ['core_objects.json']

    def setUp(self):
        self.client = Client()

    def test_fixtures(self):
        """ Tests that the fixtures actually loaded """
        assert Space.objects.all().exists()

    def test_basic_urls(self):
        """ Reverses and loads the simple TemplateViews """
        for name in ['home', 'contribute', 'needing_descriptions',
                     'needing_counterexamples', 'spaces']:
            response = self.client.get(reverse('brubeck:%s' % name))
            self.assertEqual(response.status_code, 200)

    def test_redirects(self):
        """ Tests the basic RedirectViews """
        response = self.client.get(reverse('brubeck:github'))
        self.assertEqual(response.status_code, 301)
        # Test that it really (tries to) redirect to github
        # (it's not practical to test external urls in these tests)
        self.assertEqual(response.items()[-1][1],
            'https://github.com/jamesdabbs/brubeck')

    def test_absolute_urls(self):
        """ Tests that the get_absolute_url methods of each of the basic
            objects works correctly (and that their landing pages load)
        """
        for cls in (Space, Property, Trait, Implication):
            obj = cls.objects.all()[0]
            response = self.client.get(obj.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            # Check that we got the right object
            name = obj.name() if callable(obj.name) else obj.name
            self.assertContains(response, name)

    def test_object_urls(self):
        """ Tests that the get_edit_url, get_revise_url methods reverse and
            redirect to login (if not logged in)
        """
        login = reverse('brubeck:login')
        for cls in (Space, Property, Trait, Implication):
            obj = cls.objects.all()[0]
            for foo in ('edit', 'revision'):
                url = getattr(obj, 'get_%s_url' % foo)()
                response = self.client.get(url)
                self.assertRedirects(response, '%s?next=%s' % (login, url))
            # Also, at least make sure this reverses
            self.client.get(obj.get_admin_url())

    def test_table(self):
        """ Verifies that the table view loads, but only for admins
        """
        url = reverse('brubeck:table')
        response = self.client.get(url, {'start': 1, 'end': 2})
        self.assertEqual(response.status_code, 404)

        admin = User(username='admin')
        admin.is_staff = admin.is_superuser = True
        admin.set_password('pass')
        admin.save()

        self.client.login(username='admin', password='pass')
        response = self.client.get(url, {'start': 1, 'end': 2})
        self.assertEqual(response.status_code, 200)
