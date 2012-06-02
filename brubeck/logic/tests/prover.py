from django.core.exceptions import ValidationError
from django.db.models import Model
from django.test import TestCase
from django.test.client import Client

from brubeck.logic import Formula
from brubeck.logic.utils import verify_match, get_full_proof
from brubeck.logic.formula.utils import human_to_formula
from brubeck.models import Space, Property, Trait, Implication, Value
from brubeck.utils import get_orphans, check_consistency


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

    def test_full_proof_trace(self):
        """ Tests that ~A, ~A => B, B => ~C generates ~C and examines the full
            proof trace.
        """
        # Also tests out a few variations for human_to_formula
        Implication.objects.create(
            antecedent=human_to_formula('~A'),
            consequent=human_to_formula('B=True')
        )
        Implication.objects.create(
            antecedent=human_to_formula('B'),
            consequent=human_to_formula('not C')
        )
        Trait.objects.create(space=self.space, property=self.A, value=self.F)
        verify_match(Formula(self.A, self.F) & Formula(self.B, self.T) &
            Formula(self.C, self.F), self.space)
        assert self.space.trait_set.count() == 3

        # Test the proof trace
        # The format is still somewhat in flux, but at least make sure it
        # returns a dict with with at least "id" and "name" in it
        d = get_full_proof(self.space.trait_set.get(property=self.C))[0]
        assert 'id' in d
        assert 'name' in d

        # Check that get_orphans finds both of the added traits
        assert len(get_orphans(self.space.trait_set.get(
            property=self.A))) == 2

    def test_consistency_check(self):
        """ Checks handling of implications that can be shown to be
            inconsistent
        """
        assert len(check_consistency()) == 0
        Trait.objects.create(space=self.space, property=self.A, value=self.T)
        Trait.objects.create(space=self.space, property=self.B, value=self.T)
        ant, cons = human_to_formula('A'), human_to_formula('~B')
        self.assertRaises(ValidationError, Implication.objects.create,
            antecedent=ant, consequent=cons)
        # The following will force the save of the faulty implication,
        # bypassing its save method
        Implication.objects.bulk_create([
            Implication(antecedent=ant, consequent=cons)
        ])
        assert len(check_consistency()) == 1
