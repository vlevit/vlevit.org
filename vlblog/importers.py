import codecs
import logging
import os
import os.path

from django.template import Context, Template, TemplateSyntaxError


from vlblog import models
from vlblog import utils


logger = logging.getLogger(__name__)


class TemplateLoader(object):

    TEMPLATE = (
        u"{{% load vlblog_tags %}}"
        u"{content}"
    )

    def load_template(self, path):
        with codecs.open(path, 'r', 'utf-8') as f:
            source = f.read()
        source = self.make_template_string(source)
        try:
            template = Template(source)
        except TemplateSyntaxError, e:
            template = None
            logger.error(e)
        return template

    def load_multiple_templates(self, path):
        tpl_lines = []
        with codecs.open(path, 'r', 'utf-8') as f:
            for line in f:
                if (line.startswith('---') and tpl_lines and
                        not tpl_lines[-1].strip()):
                    src = ''.join(tpl_lines)
                    tpl_lines = []
                    source = self.make_template_string(src)
                    try:
                        template = Template(source)
                    except TemplateSyntaxError, e:
                        template = None
                        logger.error(e)
                    yield template
                else:
                    tpl_lines.append(line)

    def make_template_string(self, source):
        expanded = utils.expand_template_tags(source)
        output = self.TEMPLATE.format(content=expanded)
        return output


class ConfLoaderError(Exception):
    """Common exception class for ConfLoader Errors"""


class BaseConfLoader(object):

    required = ()               # tuple of required options
    optional = {}               # default values for optional options
    types = {}                  # types for not-string options

    filename = None

    def value(self, option, raw_value):
        if option in self.types:
            kind = self.types[option]
            if kind == bool:
                return raw_value.lower() in ('true', 'yes', '1')
            else:
                raise ValueError("type {} is not supported".format(kind))
        elif option in self.optional:
            return type(self.optional[option])(raw_value)
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
                conf[entry[0]] = self.value(entry[0], entry[1])
        for p in self.required:
            if p not in conf:
                raise ConfLoaderError(u"'{}' not present in configuration {}".
                                      format(p, path))
        return conf


class BlogConfLoader(BaseConfLoader):

    required = ('blog', 'language', 'description', 'template', 'list_template')
    optional = {'file_as_name': False, 'multi_entries': False,
                'export_gplus': False, 'per_page': 1024}
    types = {'file_as_name': bool, 'multi_entries': bool, 'export_gplus': bool}

    filename = 'blog.conf'


class PagesConfLoader(BaseConfLoader):

    required = ('language', 'template')
    optional = {'file_as_name': False}
    types = {'file_as_name': bool}

    filename = 'pages.conf'


class BaseLoader(object):

    required = ()
    optional = {}

    def __init__(self, base_dir):
        self.base_dir = base_dir

    def missing_required_keys(self, data):
        return [key for key in self.required if key not in data]

    def make_data(self, template, path, conf):
        data = self.optional.copy()
        if conf['file_as_name']:
            data['name'] = utils.name_from_file(path)
        context = Context()
        body = template.render(context)
        data.update(context.get('vars', {}))
        data['body'] = utils.markdown_convert(body)
        missing = self.missing_required_keys(data)
        if missing:
            logger.error("%s: the following required fields are missing: %s",
                         path, ', '.join(missing))
            return
        return data

    def load(self, path, conf):
        data = None
        tloader = TemplateLoader()
        template = tloader.load_template(path)
        if template:
            data = self.make_data(template, path, conf)
        return data

    def load_multiple(self, path, conf):
        tloader = TemplateLoader()
        templates = tloader.load_multiple_templates(path)
        for template in templates:
            if template:
                data = self.make_data(template, path, conf)
                yield data


class PostLoader(BaseLoader):

    required = ('created', 'name')
    optional = {'title': '', 'published': None, 'excerpt': '', 'tags': []}

    def make_data(self, template, path, conf):
        data = super(PostLoader, self).make_data(template, path, conf)
        if data and data['excerpt']:
            data['excerpt'] = utils.markdown_convert(data['excerpt'])
        return data


class PageLoader(BaseLoader):

    required = ('name',)
    optional = {'title': ''}

    def make_data(self, template, path, conf):
        data = conf.copy()
        data.pop('file_as_name', None)
        page_data = super(PageLoader, self).make_data(template, path, conf)
        if page_data:
            data.update(page_data)
        else:
            data = None
        return data


class BaseImporter(object):

    tloader = None
    conf_tloader = None
    model = None

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self._file_cache = {}

    def import_entries(self, path, digest, conf):
        """
        Import entry from a file. Must be overridden by a subclass.

        """
        raise NotImplementedError

    def rename_entry(self, old_path, new_path, conf):
        """
        Rename entry identified by old_path to new_path.

        """
        file = models.File.objects.get(path=old_path)
        file.path = new_path
        file.save()
        if conf['file_as_name']:
            new_name = utils.name_from_file(new_path)
            entry = self.model.objects.get(file=file)
            entry.name = new_name
            entry.save()

    def remove_entries(self, pk):
        """
        Remove entry by pk. Must be overridden by a subclass.

        """
        raise NotImplementedError

    def get_or_create_file(self, path, digest):
        if path in self._file_cache:
            return self._file_cache[path]
        try:
            file = models.File.objects.get(path=path)
        except models.File.DoesNotExist:
            file = models.File(path=path, digest=digest)
            file.save()
        else:
            if file.digest != digest:
                file.digest = digest
                file.save()
        # keep only the last file in cache
        self._file_cache.clear()
        self._file_cache[path] = file
        return file

    def detect_changed_files(self, force_reimport):
        """
        Walk through all entries and verify if files are changed.

        self.model is expected to have File foreign key called file.

        Return tuple of unmodified, modified and removed files.
        Returned value representation:
         - unmodified files: set of absolute paths,
         - modified files: {absolute_path: digest},
         - removed files: {digest: absolute_path}

        """
        unmodified = set()
        modified = {}
        removed = {}

        # iterate through all files of self.model
        # is JOIN without WHERE clause possible with django queries?
        cond = {self.model._meta.object_name.lower() + '__pk__isnull': False}
        for file in models.File.objects.filter(**cond):
            if os.path.exists(file.path):
                digest = utils.calc_digest(file.path)
                if digest != file.digest or force_reimport:
                    modified[file.path] = digest
                else:
                    unmodified.add(file.path)
            else:
                removed[file.digest] = file.path
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
            conf_path = os.path.join(root, self.conf_loader.filename)
            if not os.path.exists(conf_path):
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
                path = os.path.join(root, filename)

                # skip untouched files
                if path in unmodified:
                    continue
                # reimport modified files
                elif path in modified:
                    digest = modified[path]
                # new file?
                else:
                    digest = utils.calc_digest(path)
                    # file renamed
                    if digest in removed:
                        old_path = removed[digest]
                        self.rename_entry(old_path, path, conf)
                        renamed.add(digest)
                        logger.info("%s renamed to %s", old_path, path)
                        continue
                    # new file
                    else:
                        n_new += 1

                # import a new file, or reimport existing file
                ok = self.import_entries(path, digest, conf)
                if not ok:
                    logger.info("%s skipped", path)
                    n_skipped += 1
                else:
                    logger.info('%s imported', path)
        for digest in set(removed).difference(renamed):
            removed_path = removed[digest]
            self.remove_entries(removed_path)
            logger.info('%s deleted', removed_path)

        logger.info("%d new files, %d changed, %d unchanged, %d removed, "
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

    def get_or_create_blog(self, conf):
        blog_key = (conf['blog'], conf['language'])
        if blog_key in self._blog_cache:
            blog = self._blog_cache[blog_key]
        else:
            data = conf.copy()
            data = {
                'name': conf['blog'],
                'language': conf['language'],
                'description': conf['description'],
                'template': conf['template'],
                'list_template': conf['list_template'],
                'export_gplus': conf['export_gplus'],
                'per_page': conf['per_page']
            }
            blog = models.Blog.get_or_create(**data)
            # keep only the last blog in cache
            self._blog_cache.clear()
            self._blog_cache[blog_key] = blog
        return blog

    def import_entries(self, path, digest, conf):
        some_imported = False
        all_imported = True
        # many posts per file
        if conf['multi_entries']:
            post_names = set()
            for data in self.loader.load_multiple(path, conf):
                if data:
                    # file and blog creation must occur only when post is
                    # loaded successfully
                    blog = self.get_or_create_blog(conf)
                    file = self.get_or_create_file(path, digest)
                    # save post
                    models.Post.insert_or_update(data, file, blog)
                    post_names.add(data['name'])
                    some_imported = True
                else:
                    all_imported = False
            all_imported = some_imported and all_imported

            # delete posts which were removed from a file
            if all_imported:
                file_posts = models.Post.objects.filter(file=file)
                removed_posts = file_posts.exclude(name__in=post_names)
                for post in removed_posts:
                    post.delete()   # clean (overridden) deletion
        # one post per file
        else:
            data = self.loader.load(path, conf)
            if data:
                blog = self.get_or_create_blog(conf)
                file = self.get_or_create_file(path, digest)
                models.Post.insert_or_update(data, file, blog)
                some_imported = True
                all_imported = True
        return some_imported

    def remove_entries(self, path):
        file = models.File.objects.get(path=path)
        removed = models.Post.objects.filter(file=file)
        for post in removed:
            post.delete()
        file.delete()


class PagesImporter(BaseImporter):

    def __init__(self, base_dir):
        super(PagesImporter, self).__init__(base_dir)
        self.loader = PageLoader(base_dir)
        self.conf_loader = PagesConfLoader()
        self.model = models.Page

    def import_entries(self, path, digest, conf):
        data = self.loader.load(path, conf)
        if not data:
            return False
        file = self.get_or_create_file(path, digest)
        try:
            page_pk = models.Page.objects.get(file=file).pk
        except models.Page.DoesNotExist:
            page_pk = None
        page = models.Page(**data)
        page.file = file
        page.pk = page_pk
        page.save()
        return True

    def remove_entries(self, path):
        # delete file and all its pages along with it
        file = models.File.objects.get(path=path)
        models.Page.objects.get(file=file).delete()
        file.delete()

