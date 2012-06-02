from django.test import TestCase

from brubeck.logic.formula.core import Formula


class FormulaTests(TestCase):
    """ Tests the basic functionality of the Formula class """
    def setUp(self):
        self.a1 = Formula(property=1, value=1)
        self.a2 = Formula(property=1, value=1)
        self.conj = self.a1 & self.a2

    def test_atom(self):
        """ Tests atom recognition and length counting """
        assert self.a1.is_atom()
        assert len(self.a1) == 1
        assert not self.conj.is_atom()
        assert len(self.conj) == 3

    def test_conj(self):
        """ Tests conjoined formulae """
        f = (self.a1 & self.a2 & self.a1) | self.a2
        assert not f.is_atom()
        assert f.operator == Formula.OR  # The top-level comparison is an OR
        assert len(f) == 6

    def test_negate(self):
        """ Tests that negation behaves as expected """
        disj = self.conj.negate()
        assert not disj.is_atom()
        assert disj.operator == Formula.OR
        assert disj.sub[0].property == 1
        assert disj.sub[0].value != 1

    def test_empty(self):
        """ Tests that formulae register as empty appropriately """
        assert Formula().is_empty()
        assert not self.a1.is_empty()
        assert not self.conj.is_empty()
