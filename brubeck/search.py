import logging
import sys

from django.conf import settings
from django.core.paginator import Paginator, Page

from pyelasticsearch import ElasticSearch


class SearchPaginator(Paginator):
    def __init__(self, query, per_page, **kwargs):
        self.query = query
        super(SearchPaginator, self).__init__([], per_page, **kwargs)

    def page(self, number):
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        result = client.search(self.query,
            **{'from': bottom, 'size': self.per_page})
        try:
            objects = result['hits']['hits']
        except KeyError:
            objects = []
        return Page(objects, number, self)

    def _get_count(self):
        if self._count is None:
            try:
                self._count = client.search(
                    self.query, **{'from': 0, 'size': 1})['hits']['total']
            except KeyError:
                self._count = 0
        return self._count
    count = property(_get_count)


class BrubeckSearch(ElasticSearch):
    def __init__(self):
        super(BrubeckSearch, self).__init__(settings.BONSAI_URL)
        self._index = settings.BONSAI_INDEX

    def get(self, doc_type, id):
        """ Retrieves the specified document """
        return super(BrubeckSearch, self).get(self._index, doc_type, id)

    def index(self, doc, doc_type, id=None):
        """ Adds the given document to the index """
        return super(BrubeckSearch, self).index(doc, self._index, doc_type, id)

    def search(self, query, body=None, doc_types=[], **query_params):
        """ Returns a SearchQueryset matching the given query """
        if not doc_types:
            doc_types = ['space', 'property', 'implication', 'trait']
        return super(BrubeckSearch, self).search(query, body=None,
            indexes=[self._index], doc_types=doc_types, **query_params)

    def delete(self, doc_type, id):
        """ Deletes a document from the index """
        return super(BrubeckSearch, self).delete(self._index, doc_type, id)

    def refresh(self):
        """ Refreshes the index """
        return super(BrubeckSearch, self).refresh(indexes=[self._index])


client = BrubeckSearch()
logger = logging.getLogger(__name__)


def index_revision(sender, instance, created, **kwargs):
    if 'test' in sys.argv:
        # No indexing, no message
        pass
    elif settings.DEBUG:
        logger.debug('Skipping indexing %s because DEBUG is on' % instance)
    else:
        s = instance.page.snippet
        name = s.object.name
        doc = {
            'name': name() if callable(name) else name,
            'text': s.current_text(),
        }
        log = client.index(doc, s.content_type.name, id=s.object_id)
        logger.debug('Indexed revision %s: %s' % (instance.id, log))


# Bulk index manipulation seems to error out after several documents.
# It seems to happen fairly consistently after ~1406 API calls. This is
# (hopefully) an issue with Bonsai limiting query rates that shouldn't be
# a problem on the live site (at least, not any time soon)
def _update_indices():
    from brubeck.models import Space, Property, Trait, Implication
    from brubeck.search import BrubeckSearch

    client = BrubeckSearch()

    for cls in [Space, Property, Trait, Implication]:
        for obj in cls.objects.all():
            r = client.get(cls.__name__.lower(), obj.id)
            text = obj.snippets.all()[0].current_text()
            if not r['exists'] or r['_source']['text'] != text:
                doc = {
                    'name': obj.name() if callable(obj.name) else obj.name,
                    'text': text
                }
                client.index(doc, cls.__name__.lower(), obj.id)
                logger.debug('Indexed: %s' % doc)


def _clear_indices():
    size = client.search('name:*')['hits']['total']
    logger.debug('Clearing %s indexed documents' % size)
    for r in client.search('name:*', size=size)['hits']['hits']:
        log = client.delete(r['_type'], r['_id'])
        logger.debug('Deleted indexed revision: %s' % log)
