import logging
import os
from os import path

from django.template.loader import BaseLoader as TemplateBaseLoader
from django.template import Context, TemplateSyntaxError


from vlblog import models
from vlblog import utils


logger = logging.getLogger(__name__)


class TemplateLoader(TemplateBaseLoader):
    is_usable = True

    TEMPLATE = (
        u"{{% load vlblog_tags %}}"
        u"{content}"
    )

    def load_template_source(self, template_name, template_dirs):
        tl_path = path.join(template_dirs[0], template_name)
        with open(tl_path) as f:
            text = f.read().decode('UTF-8')
        output = utils.expand_template_tags(text)
        output = self.TEMPLATE.format(content=output)
        return output, tl_path

    load_template_source.is_usable = True


class ConfLoaderError(Exception):
    """Common exception class for ConfLoader Errors"""


class BaseConfLoader(object):

    required = ()               # tuple of required options
    optional = {}               # default values for optional options
    types = {}                  # types for not-string options

    filename = None

    def value(self, raw_value):
        if raw_value in self.types:
            kind = self.types[raw_value]
            if kind == bool:
                return raw_value.lower() in ('true', 'yes', '1')
            else:
                raise ValueError("type {} is not supported".format(kind))
        else:
            return raw_value

    def load(self, path):
        conf = self.optional.copy()
        with open(path) as conf_file:
            conf_str = conf_file.read().decode('UTF-8')
            for line in conf_str.splitlines():
                line = line.strip()
                if not line:
                    continue
                entry = map(unicode.strip, line.split(':'))
                if len(entry) != 2:
                    raise ConfLoaderError(u"Invalid configuration syntax '{}' "
                                          "in {}".format(line, path))
                elif entry[0] not in self.required and \
                        entry[0] not in self.optional:
                    raise ConfLoaderError(u"Invalid configuration property "
                                          "'{}' in {}".format(entry[0], path))
                conf[entry[0]] = self.value(entry[1])
        for p in self.required:
            if p not in conf:
                raise ConfLoaderError(u"'{}' not present in configuration {}".
                                      format(p, path))
        return conf


class BlogConfLoader(BaseConfLoader):

    required = ('blog', 'language', 'description')
    optional = {'file_as_name': False}
    types = {'file_as_name': bool}

    filename = 'blog.conf'


class BaseLoader(object):

    required = ()
    optional = {}

    def __init__(self, base_dir):
        self.base_dir = base_dir

    def missing_required_keys(self, data):
        return [key for key in self.required if key not in data]

    def load(self, relpath, conf, digest=None):
        data = self.optional.copy()
        abspath = path.join(self.base_dir, relpath)
        tloader = TemplateLoader()
        try:
            template, _ = tloader.load_template(relpath, [self.base_dir])
        except TemplateSyntaxError, e:
            logger.error(e)
            return
        if conf['file_as_name']:
            data['name'] = utils.name_from_file(relpath)
        context = Context()
        body = template.render(context)
        data.update(context.get('vars', {}))
        data['body'] = utils.markdown_convert(body)
        data['file'] = relpath
        data['file_digest'] = digest if digest else utils.calc_digest(abspath)
        missing = self.missing_required_keys(data)
        if missing:
            logger.error("%s: the following required fields are missing: %s",
                         abspath, ', '.join(missing))
            return
        return data


class PostLoader(BaseLoader):

    required = ('created', 'name')
    optional = {'title': '', 'excerpt': '', 'tags': []}

    def load(self, relpath, file_as_name=False, digest=None):
        data = super(PostLoader, self).load(relpath, file_as_name, digest)
        if data['excerpt']:
            data['excerpt'] = utils.markdown_convert(data['excerpt'])
        return data


class BaseImporter(object):

    tloader = None
    conf_tloader = None
    model = None

    def __init__(self, base_dir):
        self.base_dir = base_dir

    def import_entry(self, relpath, conf, digest=None, pk=None):
        """
        Import entry from a file. Must be overridden by a subclass.

        """
        raise NotImplementedError

    def rename_entry(self, pk, new_relpath, conf):
        """
        Rename entry identified by pk. Must be overridden by a subclass.

        """
        raise NotImplementedError

    def remove_entry(self, pk):
        """
        Remove entry by pk. Must be overridden by a subclass.

        """
        raise NotImplementedError

    def detect_changed_files(self, force_reimport):
        """
        Walk through all entries and verify if files are changed.

        self.model is expected to have file and file_digest attributes.

        Return tuple of unmodified, modified and removed files.
        Returned value representation:
         - unmodified files: set of absolute paths,
         - modified files: {absolute_path: (primary_key, digest)},
         - removed files: {digest: (primary_key, absolute_path)}

        """
        unmodified = set()
        modified = {}
        removed = {}
        for entry in self.model.objects.all():
            abspath = path.join(self.base_dir, entry.file)
            if path.exists(abspath):
                if force_reimport:
                    modified[abspath] = (entry.pk, None)
                else:
                    digest = utils.calc_digest(abspath)
                    if digest == entry.file_digest:
                        unmodified.add(abspath)
                    else:
                        modified[abspath] = (entry.pk, digest)
            else:
                removed[entry.file_digest] = (entry.pk, abspath)
        return unmodified, modified, removed

    def import_all(self, force_reimport=False):
        """
        Walk through base directory and populate database with entries.

        """
        unmodified, modified, removed = \
            self.detect_changed_files(force_reimport)
        renamed = set()             # files renamed among 'removed' files
        n_new = n_skipped = 0       # new/skipped posts number

        for root, dirs, files in os.walk(self.base_dir):
            conf_path = path.join(root, self.conf_loader.filename)
            if not path.exists(conf_path):
                logger.info("no %s in %s, directory skipped",
                            self.conf_loader.filename, root)
                continue
            try:
                conf = self.conf_loader.load(conf_path)
            except ConfLoaderError, e:
                logger.error(unicode(e))
                logger.info("directory %s skipped", root)
                continue

            # search for all markdown files
            for filename in filter(lambda s: s.endswith('.markdown') or
                                   s.endswith('.md'), files):
                abspath = path.join(root, filename)
                relpath = abspath[len(self.base_dir) + 1:]
                digest = None
                pk = None

                # skip untouched files
                if abspath in unmodified:
                    continue
                # reimport modified files
                elif abspath in modified:
                    pk, digest = modified[abspath]
                # new file?
                else:
                    digest = utils.calc_digest(abspath)
                    # file renamed
                    if digest in removed:
                        pk, old_file = removed[digest]
                        self.rename_entry(pk, relpath, conf)
                        renamed.add(digest)
                        logger.info("%s renamed to %s", old_file, abspath)
                        continue
                    # new file
                    else:
                        n_new += 1

                ok = self.import_entry(relpath, conf, digest, pk)
                if not ok:
                    logger.info("%s skipped", abspath)
                    n_skipped += 1
                else:
                    logger.info('%s imported', abspath)
        for digest in set(removed).difference(renamed):
            pk, old_file = removed[digest]
            self.remove_entry(pk)
            logger.info('%s deleted', old_file)

        logger.info("%d new entries, %d changed, %d unchanged, %d removed, "
                    "%d renamed, %d skipped , %d imported",
                    n_new, len(modified), len(unmodified), len(removed) -
                    len(renamed), len(renamed), n_skipped, len(modified) +
                    n_new - n_skipped)


class BlogImporter(BaseImporter):

    def __init__(self, base_dir):
        super(BlogImporter, self).__init__(base_dir)
        self.loader = PostLoader(base_dir)
        self.conf_loader = BlogConfLoader()
        self.model = models.Post
        self._blog_cache = {}

    def get_blog(self, conf):
        blog_key = (conf['blog'], conf['language'])
        if blog_key in self._blog_cache:
            blog = self._blog_cache[blog_key]
        else:
            blog = models.Blog.get_or_create(
                conf['blog'], conf['language'], conf['description'])
            # keep only the last blog in cache
            self._blog_cache.clear()
            self._blog_cache[blog_key] = blog
        return blog

    def import_entry(self, relpath, conf, digest=None, pk=None):
        blog = self.get_blog(conf)
        data = self.loader.load(relpath, conf, digest)
        if not data:
            return False
        try:
            models.Post.insert_or_update(data, blog, pk)
        # TODO: replace with more specific exceptions
        except Exception, e:
            logger.exception("error while importing post: %s", e)
            return False
        return True

    def rename_entry(self, pk, new_relpath, conf):
        if conf['file_as_name']:
            new_name = utils.name_from_file(new_relpath)
        else:
            new_name = None
        models.Post.rename(pk, new_relpath, new_name)

    def remove_entry(self, pk):
        models.Post.delete(pk)
