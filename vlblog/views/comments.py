from collections import OrderedDict
import logging
import os
import os.path

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime
import yaml

from threadedcomments.models import ThreadedComment
from threadedcomments.util import safe_markdown
from vlblog import models
from vlblog import utils
from vlblog.importers import BlogConfLoader, ConfLoaderError
from utils import require_key

logger = logging.getLogger(__name__)


@require_key
def import_comments(request):
    """
    Import all comments to the database from the following locations:
        <folder>/blog/**/comments
        <folder>/pages/**/comments

    Comment file names are excepted to be the same as post/page names
    (excluding extension).

    """
    blog_info_cache = {}
    conf_loader = BlogConfLoader()

    # keep timezone info for datetime objects
    yaml.add_constructor(u'tag:yaml.org,2002:timestamp',
                         lambda cls, node: parse_datetime(node.value))

    def read_blog_info(folder):
        # read blog configuration
        blog_info = None
        blog_conf = os.path.join(folder, 'blog.conf')
        if folder in blog_info_cache:
            blog_info = blog_info_cache[folder]
        elif not os.path.exists(blog_conf):
            logger.info("no blog.conf in %s, directory skipped", folder)
        else:
            try:
                blog_info = conf_loader.load(blog_conf)
            except ConfLoaderError, e:
                logger.error(unicode(e))
                logger.info("directory %s skipped", root)
                return None
            else:
                blog_info_cache[folder] = blog_info
        return blog_info

    def load_comments(path):
        logger.info('loading %s', path)
        comments = None
        with open(path) as f:
            try:
                comments = yaml.safe_load(f)
            except yaml.YAMLError, e:
                logger.error("error loading a comment file: %s", e)
        return comments

    def extract_language_from_path(path):
        language = None
        start = path.find('/pages/')
        if start != -1:
            start += 7
            end = path.find('/', start)
            if end != -1:
                language = path[start:end]
        return language

    def import_comments_list(comments, obj, parent=None):
        # import comments to a database
        count = 0
        for c in comments:
            # consider comments with equal date to be the same
            # this makes possible to update all other comment fields
            try:
                comment = ThreadedComment.objects.get(
                    submit_date=c['published'])
            except ThreadedComment.DoesNotExist:
                comment_pk = None
            except ThreadedComment.MultipleObjectsReturned:
                logger.error("more then one comment with the same "
                             "publish date: %s", c['published'])
                continue
            else:
                comment_pk = comment.pk
            comment = ThreadedComment(
                pk=comment_pk,
                content_type=ContentType.objects.get_for_model(
                    obj.__class__),
                object_pk=unicode(obj.pk),
                user_name=c['author'],
                user_url=c.get('website', ''),
                comment=c['content'],
                submit_date=c['published'],
                site_id=settings.SITE_ID,
                is_public=True,
                is_removed=False,
                parent=parent,
                comment_html=safe_markdown(c['content']))
            comment.save()
            count += 1
            if 'replies' in c:
                count += import_comments_list(c['replies'], obj, comment)
        return count

    comments_count = 0
    comment_files_count = 0

    for root, dirs, files in os.walk(settings.BLOG_DIR):

        # we are interested only in comments directories
        if not root.endswith('/comments'):
            continue

        blog_info = read_blog_info(os.path.dirname(root))
        if not blog_info:
            continue

        # get Blog model object
        try:
            blog = models.Blog.objects.get(name=blog_info['blog'],
                                           language=blog_info['language'])
        except models.Blog.DoesNotExist:
            logger.error("blog '%s' doesn't exist", blog_info['blog'])
            continue

        # iterate through all comment files in the directory and import them to
        # the database
        for comment_file in files:
            if not comment_file.endswith('.yaml'):
                continue
            comment_file = os.path.join(root, comment_file)
            name = utils.name_from_file(comment_file)
            try:
                post = models.Post.objects.get(blog=blog, name=name)
            except models.Post.DoesNotExist:
                logger.error("post '%s' doesn't exist", name)
                continue
            comment_files_count += 1

            comments = load_comments(comment_file)
            comments_count += import_comments_list(comments, post)

    for root, dirs, files in os.walk(settings.PAGES_DIR):

        if not root.endswith('/comments'):
            continue

        language = extract_language_from_path(root)
        if not language:
            logger.error("couldn't extract language from path %s", root)
            continue

        for comment_file in files:
            if not comment_file.endswith('.yaml'):
                continue
            comment_file = os.path.join(root, comment_file)
            name = utils.name_from_file(comment_file)
            try:
                page = models.Page.objects.get(language=language, name=name)
            except models.Page.DoesNotExist:
                logger.error("page '%s' (%s) doesn't exist", name, language)
                continue
            comment_files_count += 1

            comments = load_comments(comment_file)
            comments_count += import_comments_list(comments, page)

    return HttpResponse("{0} comments imported from {1} files".format(
        comments_count, comment_files_count))


@require_key
def export_comments(request, folder='comments'):
    """
    Export all post and page comments from the database to readable yaml files.

    For every post and page with comments a single YAML file is created
    in the default storage.

    The path for post comments file is the following:
    [folder]/blog/[language]/[blog]/comments/[post].yaml

    The path for page comments file:
    [folder]/pages/[language]/comments/[page].yaml

    """

    class plain(unicode):
        """Wrapper for yaml plain style unciode representation."""

    class literal(unicode):
        """Wrapper for yaml literal style unciode representation."""

    yaml.add_representer(
        plain,
        lambda dumper, s: dumper.represent_scalar(
            u'tag:yaml.org,2002:str', s, style=''))

    yaml.add_representer(
        literal,
        lambda dumper, s: dumper.represent_scalar(
            u'tag:yaml.org,2002:str', s, style='|'))

    # keep the order of OrderedDict objects
    yaml.add_representer(OrderedDict,
                         lambda dumper, d: dumper.represent_dict(d.items()))

    def get_comment_dict(comment):
        comment_dict = OrderedDict()
        comment_dict['author'] = plain(comment.user_name)
        if comment.user_url:
            comment_dict['website'] = plain(comment.user_url)
        comment_dict['published'] = comment.submit_date
        comment_dict['content'] = literal(comment.comment)
        return comment_dict

    def get_comments_tree(comments):
        comments_tree = []      # hierarchical representation of comment dicts
        comments_map = {}       # plain mapping between id and comment itself

        for comment in comments:
            comment_dict = get_comment_dict(comment)
            if comment.parent_id not in comments_map:
                comments_tree.append(comment_dict)
            else:
                parent_dict = comments_map[comment.parent_id]
                if 'replies' not in parent_dict:
                    parent_dict['replies'] = []
                parent_dict['replies'].append(comment_dict)
            comments_map[comment.id] = comment_dict
        return comments_tree

    def get_post_path(post):
        return os.path.join(folder, 'blog', post.blog.language, post.blog.name,
                            "comments", post.name + '.yaml')

    def get_page_path(page):
        return os.path.join(folder, 'pages', page.language, page.name,
                            "comments", page.name + '.yaml')

    def dump_yaml(path, comments_tree):
        logger.info('writing %s', path)
        try:
            file = ContentFile(path)
            yaml.dump(comments_tree, file,
                      encoding='utf-8', width=80,
                      indent=4, default_flow_style=False,
                      allow_unicode=True)
            path = default_storage.save(path, file)
        except (IOError, OSError) as err:
            logger.error('error creating file %s: %s', path, err)

    comments_count = 0
    comment_files_count = 0

    for post in models.Post.objects.all():

        comments = ThreadedComment.objects.filter(
            content_type=ContentType.objects.get_for_model(models.Post),
            object_pk=post.pk,
            is_public=True,
            is_removed=False)

        comments_count += len(comments)

        comments_tree = get_comments_tree(comments)
        if comments_tree:
            path = get_post_path(post)
            dump_yaml(path, comments_tree)
            comment_files_count += 1

    for page in models.Page.objects.all():

        comments = ThreadedComment.objects.filter(
            content_type=ContentType.objects.get_for_model(models.Page),
            object_pk=page.pk,
            is_public=True,
            is_removed=False)

        comments_count += len(comments)

        comments_tree = get_comments_tree(comments)
        if comments_tree:
            path = get_page_path(page)
            dump_yaml(path, comments_tree)
            comment_files_count += 1

    return HttpResponse("{0} comments exported to {1} files".format(
        comments_count, comment_files_count))
