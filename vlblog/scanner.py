import logging
import os
import re
from os import path

from django.template.loader import BaseLoader
from django.template import Context, TemplateSyntaxError
from markdown import Markdown

from vlevitorg import settings

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
    possible = ['blog', 'lang']
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


def scan(content_dir=settings.CONTENT_DIR, force=False):
    """
    Walk through content_dir and populate database with articles.

    """
    report = []

    def log(msg, level=logging.INFO):
        logger.log(level, msg)
        report.append("{}: {}".format(logging.getLevelName(level), msg))

    loader = ArticleLoader()
    for root, dirs, files in os.walk(content_dir):
        try:
            config = parse_config(path.join(root, 'config'))
        except ConfigError, e:
            log(unicode(e), level=logging.ERROR)
            log("directory {} skipped".format(root))
            continue
        for filename in filter(lambda s: s.endswith('.markdown'), files):
            try:
                template, _ = loader.load_template(filename, [root])
            except TemplateSyntaxError, e:
                log(unicode(e), level=logging.ERROR)
                log("article {} skipped".format(path.join(root, filename)))
                continue
            context = Context()
            body = template.render(context)
            args = dict(context['vars'])
            args['body'] = body
            args.update(config)
            log('{} processed'.format(path.join(root, filename)))
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
