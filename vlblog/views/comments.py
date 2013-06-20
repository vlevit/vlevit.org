from collections import OrderedDict
import logging
import os
from os import path

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
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
def import_comments(request, blog_dir=settings.BLOG_DIR):
    """
    Import all comments found in [blog_dir]/[blog]/comments to the database.

    Name of comment file is excepted to be the same (except extension)
    as for post file.

    """

    blog_info_cache = {}
    conf_loader = BlogConfLoader()

    # keep timezone info for datetime objects
    yaml.add_constructor(u'tag:yaml.org,2002:timestamp',
                         lambda cls, node: parse_datetime(node.value))

    for root, dirs, files in os.walk(blog_dir):

        # we are interested only in comments directories
        if not root.endswith('/comments'):
            continue
        root_parent = path.dirname(root)

        # read blog configuration
        blog_conf = path.join(root_parent, 'blog.conf')
        if not path.exists(blog_conf):
            logger.info("no blog.conf in %s, directory skipped", root_parent)
            continue
        if root_parent in blog_info_cache:
            blog_info = blog_info_cache['root_parent']
        else:
            try:
                blog_info = conf_loader.load(blog_conf)
            except ConfLoaderError, e:
                logger.error(unicode(e))
                logger.info("directory %s skipped", root)
                continue
            else:
                blog_info_cache[root_parent] = blog_info

        # get Blog model object
        try:
            blog = models.Blog.objects.get(name=blog_info['blog'],
                                           language=blog_info['language'])
        except models.Blog.DoesNotExist:
            logger.error("blog '%s' doesn't exist", blog_info['blog'])
            continue

        # iterate through all comment files in the directory and import them to
        # a database
        for comment_file in files:
            if not comment_file.endswith('.yaml'):
                continue
            comment_file = path.join(root, comment_file)
            post_name = utils.name_from_file(comment_file)
            try:
                post = models.Post.objects.get(blog=blog, name=post_name)
            except models.Post.DoesNotExist:
                logger.error("post '%s' doesn't exist", post_name)
                continue

            # load comment file
            with open(comment_file) as f:
                try:
                    comments = yaml.safe_load(f)
                except yaml.YAMLError, e:
                    logger.error("error loading a comment file: %s", e)
                    continue

            def import_comment_list(comments, parent=None):
                # import comments to a database
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
                            models.Post),
                        object_pk=unicode(post.id),
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
                    if 'replies' in c:
                        import_comment_list(c['replies'], comment)

            import_comment_list(comments)

    return HttpResponse('<html><body>See log</body></html>')


@require_key
def export_comments(request, blog_dir=settings.BLOG_DIR):
    """
    Export all Post comments in database to readable yaml files.

    One yaml file is created per post with comments and is put under
    [blog_dir]/[language]/[blog]/exported_comments directory.

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

    def make_comment_dict(comment):
        comment_dict = OrderedDict()
        comment_dict['author'] = plain(comment.user_name)
        if comment.user_url:
            comment_dict['website'] = plain(comment.user_url)
        comment_dict['published'] = comment.submit_date
        comment_dict['content'] = literal(comment.comment)
        return comment_dict

    for post in models.Post.objects.all():

        comments = ThreadedComment.objects.filter(
            content_type=ContentType.objects.get_for_model(models.Post),
            object_pk=post.pk)

        comment_list = []       # hierarchical representation of comment dicts
        comment_ref = {}        # plain mapping between id and comment itself

        for comment in comments:
            comment_dict = make_comment_dict(comment)
            if comment.parent_id not in comment_ref:
                comment_list.append(comment_dict)
            else:
                parent_dict = comment_ref[comment.parent_id]
                if 'replies' not in parent_dict:
                    parent_dict['replies'] = []
                parent_dict['replies'].append(comment_dict)
            comment_ref[comment.id] = comment_dict

        if comment_list:
            comment_dir = path.join(blog_dir, post.blog.language,
                                    post.blog.name, "exported_comments")
            if not path.exists(comment_dir):
                try:
                    os.mkdir(comment_dir)
                except OSError:
                    logger.error('error while creating %s', comment_dir)
                    continue
            comment_file = path.join(comment_dir, post.name + '.yaml')
            with open(comment_file, 'w') as f:
                yaml.dump(comment_list, f, encoding='utf-8', width=80,
                          indent=4, default_flow_style=False,
                          allow_unicode=True)

    return HttpResponse('<html><body>See log</body></html>')
