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
markdown = Markdown(extensions=['footnotes', 'toc', 'codehilite'])


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
        output = preprocess_source(text)
        output = POST_TEMPLATE.format(content=output)
        return output, tl_path

    load_template_source.is_usable = True


class BlogInfoError(Exception): pass


def read_blog_info(config_path):
    """Parse blog config. Raise BlogInfoError."""
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
                    raise BlogInfoError(u"Invalid blog config syntax '{}' "
                                        "in {}".format(line, config_path))
                elif entry[0] not in possible:
                    raise BlogInfoError(u"Invalid blog config property '{}'"
                                        " in {}".format(entry[0], config_path))
                config[entry[0]] = entry[1]
    for p in possible:
        if p not in config:
            raise BlogInfoError(u"'{}' not present in blog config {}".
                                format(p, config_path))
    return config


@transaction.commit_on_success
def save_post(post_dict, blog_info, post_pk=None):
    """
    Add a new post to the database or if post_pk is not None, update
    that post.

    """
    try:
        blog = models.Blog.objects.get(name=blog_info['blog'])
    except models.Blog.DoesNotExist:
        blog = models.Blog(name=blog_info['blog'],
                           description=blog_info['description'])
        blog.save()
    else:
        if blog.description != blog_info['description']:
            blog.description = blog_info['description']
            blog.save()
    tags = []
    if post_pk is not None:         # remove tags
        post = models.Post.objects.get(pk=post_pk)
        post.clear_tags()
    for tagname in post_dict['tags']:
        tag = models.Tag.new_tag(tagname, blog, blog_info['language'])
        tag.save()
        tags.append(tag)
    post = models.Post(
        file=post_dict['file'],
        file_digest=post_dict['file_digest'],
        blog=blog,
        language=blog_info['language'],
        post_id=post_dict['post_id'],
        created=post_dict['created'],
        title=post_dict['title'],
        body=post_dict['body'],
        excerpt=post_dict['excerpt']
    )
    post.pk = post_pk
    post.save()
    post.tags.add(*tags)


def rename_post(post_pk, new_file):
    post = models.Post.objects.get(pk=post_pk)
    post.file = new_file
    post.save()


def delete_post(post_pk):
    models.Post.objects.get(pk=post_pk).delete()


def calc_digest(path):
    with open(path) as f:
        text = f.read()
        return hashlib.sha1(text).hexdigest()


def load_post(content_dir, relpath, digest=None):

    def add_missing_keys(post_dict):
        optional = ('title', 'excerpt', 'post_id')
        for key in optional:
            if key not in post_dict:
                post_dict[key] = ''
        if 'tags' not in post_dict:
            post_dict['tags'] = []
        return True

    def missing_required_keys(post_dict):
        required = ('created',)
        return [key for key in required if key not in post_dict]

    abspath = path.join(content_dir, relpath)
    loader = PostLoader()
    try:
        template, _ = loader.load_template(relpath, [content_dir])
    except TemplateSyntaxError, e:
        logger.error(e)
        return
    context = Context()
    body = template.render(context)
    post_dict = dict(context.get('vars', {}))
    post_dict['body'] = body
    post_dict['file'] = relpath
    post_dict['file_digest'] = digest if digest else calc_digest(abspath)
    add_missing_keys(post_dict)
    missing = missing_required_keys(post_dict)
    if missing:
        logger.error("%s: the following required fields are missing: %s",
                     abspath, ', '.join(missing))
        return
    return post_dict


def detect_changes(content_dir):
    unmodified = set()
    modified = {}
    removed = {}
    for post in models.Post.objects.all():
        abspath = path.join(content_dir, post.file)
        if path.exists(abspath):
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
        try:
            blog_info = read_blog_info(path.join(root, 'blog.conf'))
        except BlogInfoError, e:
            logger.error(unicode(e))
            logger.info("directory %s skipped", root)
            continue
        for filename in filter(lambda s: s.endswith('.markdown'), files):
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
                if digest in removed:  # file renamed
                    post_pk, old_file = removed[digest]
                    rename_post(post_pk, relpath)
                    renamed.add(digest)
                    logger.info("%s renamed to %s", old_file, relpath)
                    continue
                else:
                    n_new += 1
            post_dict = load_post(content_dir, relpath, digest=digest)
            if not post_dict:
                logger.info("%s skipped", abspath)
                n_skipped += 1
                continue
            try:
                save_post(post_dict, blog_info, post_pk=post_pk)
            except Exception, e:
                n_skipped += 1
                logger.exception('%s skipped: %s', abspath, e)
            else:
                logger.info('%s imported', abspath)
    for digest in set(removed).difference(renamed):
        post_pk, old_file = removed[digest]
        delete_post(post_pk)
        logger.info('%s deleted', old_file)
    logger.info("%d new posts, %d changed, %d unchanged, %d removed, "
                "%d renamed, %d skipped , %d imported", n_new, len(modified),
                len(unmodified), len(removed) - len(renamed), len(renamed),
                n_skipped, len(modified) + n_new - n_skipped)


def scan(content_dir=settings.CONTENT_DIR):
    unmodified, modified, removed = detect_changes(content_dir)
    scan_filesystem(content_dir, unmodified, modified, removed)


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
