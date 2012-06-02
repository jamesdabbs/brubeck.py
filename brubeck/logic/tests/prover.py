from django.test import TestCase
from django.test.client import Client

from brubeck.logic import Formula
from brubeck.logic.utils import verify_match
from brubeck.logic.formula.utils import human_to_formula
from brubeck.models import Space, Property, Trait, Implication, Value


class ProverTests(TestCase):
    """ Tests the automated theorem prover """
    fixtures = ['values.json']

    def setUp(self):
        self.client = Client()

        # Set up enough data points to start
        self.space = Space.objects.create(name='space')
        for name in ['A', 'B', 'C']:
            setattr(self, name, Property.objects.create(name=name))
        self.T = Value.objects.get(name='True')
        self.F = Value.objects.get(name='False')

    def test_direct_implication(self):
        """ Tests that A & A => B creates B """
        Implication.objects.create(
            antecedent=human_to_formula('A'),
            consequent=human_to_formula('B')
        )
        Trait.objects.create(space=self.space, property=self.A, value=self.T)
        verify_match(Formula(self.B, self.T), self.space)
        assert self.space.trait_set.count() == 2

    def test_contrapositive_implication(self):
        """ Tests that ~B & A => B creates ~A """
        Implication.objects.create(
            antecedent=human_to_formula('A'),
            consequent=human_to_formula('B')
        )
        Trait.objects.create(space=self.space, property=self.B, value=self.F)
        verify_match(Formula(self.A, self.F), self.space)
        assert self.space.trait_set.count() == 2

    def test_conjunction(self):
        """ Tests A => B + C """
        # Test the forward direction
        Implication.objects.create(
            antecedent=human_to_formula('A'),
            consequent=human_to_formula('B + C')
        )
        Trait.objects.create(space=self.space, property=self.A, value=self.T)
        verify_match(Formula(self.B, self.T) & Formula(self.C, self.T),
            self.space)
        assert self.space.trait_set.count() == 3

        # Also test the contrapositive
        Trait.objects.all().delete()
        Trait.objects.create(space=self.space, property=self.C, value=self.F)
        verify_match(Formula(self.A, self.F), self.space)
        assert self.space.trait_set.count() == 2

    def test_disjunction(self):
        """ Tests A => B | C """
        # The forward direction
        Implication.objects.create(
            antecedent=human_to_formula('A'),
            consequent=human_to_formula('B | C')
        )
        Trait.objects.create(space=self.space, property=self.A, value=self.T)
        assert self.space.trait_set.count() == 1
        Trait.objects.create(space=self.space, property=self.C, value=self.F)
        verify_match(Formula(self.B, self.T), self.space)
        assert self.space.trait_set.count() == 3

        # And the contrapositive
        Trait.objects.all().delete()
        Trait.objects.create(space=self.space, property=self.B, value=self.F)
        Trait.objects.create(space=self.space, property=self.C, value=self.F)
        verify_match(Formula(self.A, self.F), self.space)
        assert self.space.trait_set.count() == 3
