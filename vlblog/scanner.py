import hashlib
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


POST_TEMPLATE = (
    u"{{% load vlblog_tags %}}"
    u"{content}"
)


class PostLoader(BaseLoader):
    is_usable = True

    def load_template_source(self, template_name, template_dirs):
        tl_path = path.join(template_dirs[0], template_name)
        with open(tl_path) as f:
            text = f.read().decode('UTF-8')
        output = expand_template_tags(text)
        output = POST_TEMPLATE.format(content=output)
        return output, tl_path

    load_template_source.is_usable = True


class BlogInfoError(Exception): pass


def read_blog_info(config_path):
    """Parse blog config. Raise BlogInfoError."""
    required = ['blog', 'language', 'description']
    optional = ['file_as_name']
    config = {}
    with open(config_path) as config_file:
        config_str = config_file.read().decode('UTF-8')
        for line in config_str.splitlines():
            line = line.strip()
            if not line:
                continue
            entry = map(unicode.strip, line.split(':'))
            if len(entry) != 2:
                raise BlogInfoError(u"Invalid blog config syntax '{}' "
                                    "in {}".format(line, config_path))
            elif entry[0] not in required and entry[0] not in optional:
                raise BlogInfoError(u"Invalid blog config property '{}'"
                                    " in {}".format(entry[0], config_path))
            config[entry[0]] = entry[1]
    for p in required:
        if p not in config:
            raise BlogInfoError(u"'{}' not present in blog config {}".
                                format(p, config_path))
    if ('file_as_name' in config and
            config['file_as_name'].lower() in ('true', 'yes', '1')):
        config['file_as_name'] = True
    else:
        config['file_as_name'] = False
    return config


def calc_digest(path):
    with open(path) as f:
        text = f.read()
        return hashlib.sha1(text).hexdigest()


def name_from_file(relpath):
    basename = path.basename(relpath)
    return re.sub('[^\w-]', '-', basename[:basename.rfind('.')])


def load_post(content_dir, relpath, file_as_name=False, digest=None):

    def add_missing_keys(post_dict):
        optional = ('title', 'excerpt')
        for key in optional:
            if key not in post_dict:
                post_dict[key] = ''
        if 'tags' not in post_dict:
            post_dict['tags'] = []
        return True

    def missing_required_keys(post_dict):
        required = ('created', 'name')
        return [key for key in required if key not in post_dict]

    abspath = path.join(content_dir, relpath)
    loader = PostLoader()
    try:
        template, _ = loader.load_template(relpath, [content_dir])
    except TemplateSyntaxError, e:
        logger.error(e)
        return
    post_dict = {}
    if file_as_name:
        post_dict['name'] = name_from_file(relpath)
    context = Context()
    body = template.render(context)
    post_dict.update(context.get('vars', {}))
    if 'excerpt' in post_dict:
        post_dict['excerpt'] = markdown_convert(post_dict['excerpt'])
    post_dict['body'] = markdown_convert(body)
    post_dict['file'] = relpath
    post_dict['file_digest'] = digest if digest else calc_digest(abspath)
    add_missing_keys(post_dict)
    missing = missing_required_keys(post_dict)
    if missing:
        logger.error("%s: the following required fields are missing: %s",
                     abspath, ', '.join(missing))
        return
    return post_dict


def detect_changes(content_dir, force_reimport=False):
    unmodified = set()
    modified = {}
    removed = {}
    for post in models.Post.objects.all():
        abspath = path.join(content_dir, post.file)
        if path.exists(abspath):
            if force_reimport:
                modified[abspath] = (post.pk, None)
            else:
                digest = calc_digest(abspath)
                if digest == post.file_digest:
                    unmodified.add(abspath)
                else:
                    modified[abspath] = (post.pk, digest)
        else:
            removed[post.file_digest] = (post.pk, post.file)
    return unmodified, modified, removed


def scan_filesystem(content_dir, unmodified=set(), modified={}, removed={}):
    """
    Walk through content_dir and populate database with articles.

    """
    renamed = set()             # files renamed among 'removed' files
    n_new = n_skipped = 0       # new/skipped posts number
    for root, dirs, files in os.walk(content_dir):
        blog_conf = path.join(root, 'blog.conf')
        if not path.exists(blog_conf):
            logger.info("no blog.conf in %s, directory skipped", root)
            continue
        try:
            blog_info = read_blog_info(blog_conf)
        except BlogInfoError, e:
            logger.error(unicode(e))
            logger.info("directory %s skipped", root)
            continue
        blog = models.Blog.get_or_create(
            blog_info['blog'], blog_info['language'], blog_info['description'])
        for filename in filter(lambda s: s.endswith('.markdown') or
                               s.endswith('.md'), files):
            abspath = path.join(root, filename)
            relpath = abspath[len(content_dir) + 1:]
            digest = None
            post_pk = None
            if abspath in unmodified:
                continue
            elif abspath in modified:
                post_pk, digest = modified[abspath]
            else:
                digest = calc_digest(abspath)
                logger.debug("%s digest: %s", relpath, digest)
                if digest in removed:  # file renamed
                    post_pk, old_file = removed[digest]
                    new_name = None
                    if blog_info['file_as_name']:
                        new_name = name_from_file(relpath)
                    models.Post.rename(post_pk, relpath, new_name)
                    renamed.add(digest)
                    logger.info("%s renamed to %s", old_file, relpath)
                    continue
                else:
                    n_new += 1
            post_dict = load_post(content_dir, relpath,
                                  blog_info['file_as_name'], digest=digest)
            if not post_dict:
                logger.info("%s skipped", abspath)
                n_skipped += 1
                continue
            try:
                models.Post.insert_or_update(post_dict, blog, post_pk)
            except Exception, e:
                n_skipped += 1
                logger.exception('%s skipped: %s', abspath, e)
            else:
                logger.info('%s imported', abspath)
    for digest in set(removed).difference(renamed):
        post_pk, old_file = removed[digest]
        models.Post.delete(post_pk)
        logger.info('%s deleted', old_file)
    logger.info("%d new posts, %d changed, %d unchanged, %d removed, "
                "%d renamed, %d skipped , %d imported", n_new, len(modified),
                len(unmodified), len(removed) - len(renamed), len(renamed),
                n_skipped, len(modified) + n_new - n_skipped)


def scan(content_dir=settings.CONTENT_DIR, force_reimport=False):
    unmodified, modified, removed = detect_changes(content_dir, force_reimport)
    scan_filesystem(content_dir, unmodified, modified, removed)


TAG_RE = re.compile(r'/(?P<tag>\w+)(:\s*(?P<value>.*))?\s*$', re.UNICODE)


def expand_template_tags(source):
    """
    Replace short tags with django templates tags

    Example:
    /tag: value
    is replaced with
    {% tag "value" %}

    """
    result = []
    for line in source.splitlines():
        m = TAG_RE.match(line)
        if m:
            tag, value = m.group('tag'), m.group('value')
            if value:
                result.append(u"{{% {} \"{}\" %}}".format(tag, value))
            else:
                result.append(u"{{% {} %}}".format(tag))
        else:
            result.append(line + u'\n')
    return u''.join(result)


def attr_list_strict():
    """
    Attribute Lists Markdown Extension Hack

    Syntax for attribute list is {: ... }, but the colon is optional. This
    syntax clashes with django templates (the extension interprets django tags
    as attribute lists). This hack makes the colon mandatory.

    """
    import markdown.extensions.attr_list as al
    BASE_RE = r'\{\:([^\}]*)\}'
    al.AttrListTreeprocessor.HEADER_RE = re.compile(r'[ ]*%s[ ]*$' % BASE_RE)
    al.AttrListTreeprocessor.BLOCK_RE = re.compile(r'\n[ ]*%s[ ]*$' % BASE_RE)
    al.AttrListTreeprocessor.INLINE_RE = re.compile(r'^%s' % BASE_RE)
    return al.AttrListExtension()


def markdown_convert(source):
    """
    Return a valid django template for markdown-formatted source.

    """
    markdown = Markdown(output_format='html5',
                        extensions=['footnotes', 'toc',
                                    'codehilite', attr_list_strict()])
    return markdown.convert(source)
