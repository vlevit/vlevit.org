from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import httplib2
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError, FlowExchangeError, \
    OAuth2WebServerFlow


class Command(BaseCommand):
    help = "Authorize Google Plus user and save credentials " \
           "(access and refresh tokens) on disk."

    option_list = BaseCommand.option_list + (
        make_option('--force',
            action='store_true',
            dest='force',
            default=False,
            help="Force Google+ authorization flow even if access token "
                 "is valid."),
        )

    def handle(self, *args, **options):

        flow = OAuth2WebServerFlow(
            client_id=settings.GPLUS_CLIENT_ID,
            client_secret=settings.GPLUS_CLIENT_SECRET,
            redirect_uri=settings.GPLUS_REDIRECT_URL,
            scope='https://www.googleapis.com/auth/plus.login',
            request_visible_actions='http://schema.org/CreateAction',
            access_type='offline',
            approval_prompt='force')

        storage = Storage(settings.GPLUS_CREDENTIALS_FILE)
        credentials = storage.get()

        if credentials is None or credentials.invalid or options['force']:
            if credentials is None:
                self.stdout.write("no credentials found")
            elif credentials.invalid:
                self.stdout.write("credentials are invalid")
            self.stdout.write("start authorization flow")
            url = flow.step1_get_authorize_url()
            print("Authorization URL: %s" % url)
            try:
                code = raw_input("Code:")
            except EOFError:
                code = None
            if not code:
                raise CommandError("Authorization flow interrupted")
            try:
                credentials = flow.step2_exchange(code)
            except FlowExchangeError as e:
                raise CommandError(e)
            else:
                storage.put(credentials)
                self.stdout.write("credential updated successfully")
        else:
            self.stdout.write("credentials are valid")
            if credentials.refresh_token and credentials.access_token_expired:
                self.stdout.write("update access token")
                http = httplib2.Http()
                http = credentials.authorize(http)
                try:
                    credentials.refresh(http)
                except AccessTokenRefreshError as e:
                    self.stdout.write("update failed: %s" % e)
                else:
                    self.stdout.write("access token updated successfully")
            elif not credentials.refresh_token:
                self.stdout.write("no refresh token, can't update access token")
            else:
                self.stdout.write("access token is not expired yet, no need "
                                 "to refresh")
