import logging

from apiclient.discovery import build
from apiclient.errors import HttpError
from django.contrib.sites.models import Site
import httplib2
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError

from vlblog.models import Post

logger = logging.getLogger(__name__)


class GPlusExporter(object):

    def __init__(self, credentials_file):
        self.credentials_file = credentials_file
        self.storage = Storage(credentials_file)
        self.credentials = self.storage.get()

    def export(self):
        http = self._get_authorized_http()
        if not http:
            return 0

        plus = build('plus', 'v1', http=http)
        moments = {}
        request = plus.moments().list(userId='me', collection='vault')
        while request is not None:
            response = request.execute()
            for item in response.get('items', []):
                moments[item['url']] = item
            request = plus.moments().list_next(request, response)

        posts = Post.objects.filter(blog__export_gplus='tech')
        inserted = 0
        for post in posts:
            url = 'http://{domain}{path}'.format(
                domain=Site.objects.get_current().domain,
                path=post.get_absolute_url())
            if url not in moments:
                moment = {
                    'type': 'http://schema.org/CreateAction',
                    'startDate': post.created.isoformat(),
                    'object': {
                        'url': url
                    }
                }
                request = plus.moments().insert(
                    userId='me', collection='vault', body=moment)
                try:
                    request.execute()
                except HttpError:
                    logger.exception("error exporting post %s", post)
                    break
                logger.info("imported %s", post)
                inserted += 1
        return inserted

    def _get_authorized_http(self):
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        if self.credentials.access_token_expired:
            try:
                self.credentials.refresh(http)
            except AccessTokenRefreshError as e:
                logger.error("Refresh access token failed: %s" % e)
                http = None
            else:
                http = self.credentials.authorize(http)
        return http
