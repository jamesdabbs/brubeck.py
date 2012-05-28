import logging

from django.conf import settings

from pyelasticsearch import ElasticSearch


class BrubeckSearch(ElasticSearch):
    def __init__(self):
        super(BrubeckSearch, self).__init__(settings.BONSAI_URL)
        self._index = settings.BONSAI_INDEX

    def index(self, doc, doc_type, id=None):
        return super(BrubeckSearch, self).index(doc, self._index, doc_type, id)


client = BrubeckSearch()
logger = logging.getLogger(__name__)


def index_revision(sender, instance, created, **kwargs):
    s = instance.page.snippet
    name = s.object.name
    doc = {
        'name': name() if callable(name) else name,
        'text': s.current_text(),
    }
    log = client.index(doc, s.content_type.name, id=s.object_id)
    logger.debug('Indexed revision: %s' % log)


def _build_indicies():
    from brubeck.models import Revision

    for r in Revision.objects.all():
        index_revision(Revision, r, False)