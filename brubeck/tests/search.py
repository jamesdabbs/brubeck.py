# Tests functionality related to bonsai elasticsearch
from django.test import TestCase

from brubeck.search import BrubeckSearch


class SearchTest(TestCase):
    def test_indexing(self):
        """ Tests that documents are stored and deleted properly in the index
        """
        client = BrubeckSearch()

        doc = {
            'id': 1,
            'type': 'bonsai-test-document',
            'name': 'test-name'
        }

        # Delete the document (in case it already exists from partial test)
        client.delete(doc['type'], doc['id'])

        # Verify that the document does not exist
        assert not client.get(doc['type'], doc['id'])['exists']

        # Add it and test that it now does exist
        client.index(doc, doc['type'], doc['id'])
        client.refresh()
        assert client.get(doc['type'], doc['id'])['exists']

        # Search for it
        assert client.search('name:%s' % doc['name'], doc_types=[doc['type']])[
               'hits']['total'] == 1

        # Delete it
        client.delete(doc['type'], doc['id'])

        # And make sure it was deleted
        assert not client.get(doc['type'], doc['id'])['exists']
