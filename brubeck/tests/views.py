# Tests the core brubeck views
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from brubeck.logic.formula.utils import human_to_formula
from brubeck.models import Space, Property, Trait, Implication, Value


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
