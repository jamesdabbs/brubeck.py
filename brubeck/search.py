import logging

from django.conf import settings

from pyelasticsearch import ElasticSearch


class BrubeckSearch(ElasticSearch):
    def __init__(self):
        super(BrubeckSearch, self).__init__(settings.BONSAI_URL)
        self._index = settings.BONSAI_INDEX

    def index(self, doc, doc_type, id=None):
        return super(BrubeckSearch, self).index(doc, self._index, doc_type, id)

    def search(self, query, body=None, doc_types=[], **query_params):
        if not doc_types:
            doc_types = ['space', 'property', 'implication', 'trait']
        return super(BrubeckSearch, self).search(query, body=None,
            indexes=[self._index], doc_types=doc_types, **query_params)

    def delete(self, doc_type, id):
        return super(BrubeckSearch, self).delete(self._index, doc_type, id)


client = BrubeckSearch()
logger = logging.getLogger(__name__)


def index_revision(sender, instance, created, **kwargs):
    if settings.DEBUG:
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
def _build_indices(start=None, end=None):
    from brubeck.models import Revision

    revisions = Revision.objects.all().order_by('id')
    if start:
        revisions = revisions.filter(id__gte=start)
    if end:
        revisions = revisions.filter(id__lte=end)
    for r in revisions:
        r.save()  # index_revision is a post_save method. This will also
                  # update the proof_text if possible.


def _clear_indices():
    size = client.search('name:*')['hits']['total']
    logger.debug('Clearing %s indexed documents' % size)
    for r in client.search('name:*', size=size)['hits']['hits']:
        log = client.delete(r['_type'], r['_id'])
        logger.debug('Deleted indexed revision: %s' % log)
