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
        for cls in [Space, Property, Trait, Implication]:
            obj = cls.objects.all()[0]
            response = self.client.get(obj.get_absolute_url())
            self.assertEqual(response.status_code, 200)
            # Check that we got the right object
            name = obj.name() if callable(obj.name) else obj.name
            self.assertContains(response, name)


class ValueTests(TestCase):
    """ Tests that the expected value objects have been created (by a data
        migration).
    """
    def test_values(self):
        """ Tests that 'boolean', 'True' and 'False' exist and have their
            intended ids.
        """
        v = ValueSet.objects.get(id=ValueSet.BOOLEAN, name='boolean')
        Value.objects.get(id=Value.TRUE, name='True', value_set=v)
        Value.objects.get(id=Value.FALSE, name='False', value_set=v)