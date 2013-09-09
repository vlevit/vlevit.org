import os.path as path

proj_dir = path.dirname(path.dirname(__file__))

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

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = path.join(proj_dir, 'media/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
MEDIA_URL = "/media/"

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = path.join(proj_dir, 'staticfiles/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

# Make this unique, and don't share it with anybody.
SECRET_KEY = ""

SECRET_URL_KEY = ""
