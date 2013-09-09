DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/path/to/db.sqlite'
    }
}

ENVIRON_REDIRECTIONS = (
    ("^examlpe", "http://example.com"),
)

ADMINS = (("Jane Doe", "jane.doe@example.com"),)
MANAGERS = ADMINS

ALLOWED_HOSTS = ".example.com"

SERVER_EMAIL = "robot@example.com"
EMAIL_HOST = "mail.example.com"
EMAIL_PORT = "25"
EMAIL_HOST_USER = "robot@example.com"
EMAIL_HOST_PASSWORD = "password"
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = "[Django][example.com] "
SEND_BROKEN_LINK_EMAILS = True

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

# Make this unique, and don't share it with anybody.
SECRET_KEY = ""

SECRET_URL_KEY = ""
