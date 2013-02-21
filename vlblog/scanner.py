import logging
import os
import re
from os import path

from django.template.loader import BaseLoader
from django.template import Context, TemplateSyntaxError
from django.db import transaction
from markdown import Markdown

from vlevitorg import settings
from vlblog import models


logger = logging.getLogger(__name__)
markdown = Markdown(extensions=['footnotes', 'toc', 'codehilite'])


ARTICLE_TEMPLATE = (
    u"{{% load vlblog_tags %}}"
    u"{content}"
)


class ArticleLoader(BaseLoader):
    is_usable = True

    def load_template_source(self, template_name, template_dirs):
        tl_path = path.join(template_dirs[0], template_name)
        with open(tl_path) as f:
            text = f.read().decode('UTF-8')
        output = preprocess_source(text)
        output = ARTICLE_TEMPLATE.format(content=output)
        return output, tl_path

    load_template_source.is_usable = True


class ConfigError(Exception): pass


def parse_config(config_path):
    """Parse articles' config. Raise ConfigError."""
    possible = ['blog', 'language', 'description']
    config = {}
    if os.path.exists(config_path):
        with open(config_path) as config_file:
            config_str = config_file.read().decode('UTF-8')
            for line in config_str.splitlines():
                line = line.strip()
                if not line:
                    continue
                entry = map(unicode.strip, line.split(':'))
                if len(entry) != 2:
                    raise ConfigError(u"Invalid article config syntax '{}' "
                                      "in {}".format(line, config_path))
                elif entry[0] not in possible:
                    raise ConfigError(u"Invalid article config property '{}' "
                                      "in {}".format(entry[0], config_path))
                config[entry[0]] = entry[1]
    for p in possible:
        if p not in config:
            raise ConfigError(u"'{}' not present in article config {}".
                              format(p, config_path))
    return config


@transaction.commit_on_success
def _add_new_post(post):
    try:
        blog = models.Blog.objects.get(name=post['blog'])
    except models.Blog.DoesNotExist:
        blog = models.Blog(name=post['blog'],
                           description=post['description'])
        blog.save()
    tags = []
    for tag in post['tags']:
        try:
            tag_model = models.Tag.objects.get(name=tag, blog=blog,
                                               language=post['language'])
        except models.Tag.DoesNotExist:
            tag_model = models.Tag(name=tag, blog=blog,
                                   language=post['language'])
        tag_model.n_posts += 1
        tag_model.save()
        tags.append(tag_model)
    post = models.Post(blog=blog, language=post['language'],
                       post_id=post['post_id'], created=post['created'],
                       title=post['title'], body=post['body'],
                       excerpt=post['excerpt'])
    post.save()
    post.tags.add(*tags)


def scan(content_dir=settings.CONTENT_DIR, force=False):
    """
    Walk through content_dir and populate database with articles.

    """
    report = []

    def log(msg, level=logging.INFO):
        logger.log(level, msg)
        report.append("{}: {}".format(logging.getLevelName(level), msg))

    def add_missing_keys(post):
        optional = ('title', 'excerpt', 'post_id')
        for key in optional:
            if key not in post:
                post[key] = ''
        if 'tags' not in post:
            post['tags'] = []
        return True

    def missing_required_keys(post):
        required = ('created',)
        return [key for key in required if key not in post]

    loader = ArticleLoader()
    for root, dirs, files in os.walk(content_dir):
        try:
            config = parse_config(path.join(root, 'config'))
        except ConfigError, e:
            log(unicode(e), level=logging.ERROR)
            log("directory {} skipped".format(root))
            continue
        for filename in filter(lambda s: s.endswith('.markdown'), files):
            abspath = path.join(root, filename)
            try:
                template, _ = loader.load_template(filename, [root])
            except TemplateSyntaxError, e:
                log(unicode(e), level=logging.ERROR)
                log("article {} skipped".format(path.join(root, filename)))
                continue
            context = Context()
            body = template.render(context)
            post = dict(context['vars'])
            post['body'] = body
            post.update(config)
            add_missing_keys(post)
            missing = missing_required_keys(post)
            if missing:
                log("{} skipped: the following fields are missing: {}".format(
                    abspath, ', '.join(missing)))
                continue
            try:
                _add_new_post(post)
            except Exception, e:
                log('{} skipped: {}'.format(abspath, unicode(e)),
                    level=logging.ERROR)
            else:
                log('{} processed'.format(abspath))
    return u'\n'.join(report)


TAG_RE = re.compile(r'/(?P<tag>\w+)(:\s*(?P<value>.*))?\s*$', re.UNICODE)


def _replace_tags(source):
    """
    Replace short tags with django templates tags

    Example:
    /tag: value
    is replaced with
    {% tag "value" %}

    """
    lines = source.splitlines()
    for i, line in enumerate(lines):
        m = TAG_RE.match(line)
        if m:
            tag, value = m.group('tag'), m.group('value')
            if value:
                lines[i] = u"{{% {} \"{}\" %}}".format(tag, value)
            else:
                lines[i] = u"{{% {} %}}".format(tag)
    return u'\n'.join(lines)


def preprocess_source(source):
    """
    Return a valid django template for markdown-formatted source.

    """
    output = _replace_tags(source)
    return markdown.convert(output)
