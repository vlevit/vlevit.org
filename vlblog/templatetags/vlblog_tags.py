import logging

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.dateparse import parse_datetime

import utils


logger = logging.getLogger(__name__)


register = template.Library()


def unquoted_tag(func=None, name=None):
    function_name = name or getattr(func, '_decorated_function', func).__name__

    class Node(template.Node):
        def __init__(self, func, value):
            self.func = func
            self.value = value

        def render(self, context):
            return self.func(context, self.value)

    def wrap_func(func):
        def tag_func(parser, token):
            tag, contents = token.contents.split(' ', 1)
            contents = utils.unquote_string(contents)
            return Node(func, contents)
        register.tag(function_name, tag_func)
        return func

    if func is None:            # @unquoted_tag(...)
        return wrap_func
    elif callable(func):        # @unquoted_tag
        return wrap_func(func)
    else:
        raise TypeError("Invalid arguments provided to unquoted_tag")


@unquoted_tag
def title(context, value):
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['title'] = value
    return u''


def datetag(context, value, var):
    try:
        dt = parse_datetime(value)
    except ValueError:
        dt = None
    if not dt:
        logger.warning('in template: invalid date: %s', value)
        return u''
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars'][var] = dt
    return u''


@unquoted_tag
def created(context, value):
    return datetag(context, value, 'created')


@unquoted_tag
def published(context, value):
    return datetag(context, value, 'published')


@unquoted_tag
def tags(context, value):
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['tags'] = map(
        lambda s: s.strip(), value.split(','))
    return u''


@unquoted_tag
def name(context, value):
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['name'] = value
    return u''


@unquoted_tag(name='template')
def template_tag(context, value):
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['template'] = value
    return u''


class ExcerptNode(template.Node):

    def __init__(self, nodelist, show='off'):
        self.nodelist = nodelist
        self.show = show

    def render(self, context):
        excerpt = self.nodelist.render(context)
        if 'vars' not in context.dicts[0]:
            context.dicts[0]['vars'] = {}
        context.dicts[0]['vars']['excerpt'] = excerpt
        if self.show == 'on':
            return excerpt
        return u''


@register.tag
def excerpt(parser, token):
    show = 'off'
    cont = token.split_contents()
    if len(cont) > 1:
        show = cont[1]
    nodelist = parser.parse(('endexcerpt', ))
    parser.delete_first_token()
    return ExcerptNode(nodelist, show)


class ImageNode(template.Node):

    html = u"""<img src="{static}images/{src}" alt="{alt}">"""

    def __init__(self, src, alt):
        self.src = src
        self.alt = alt

    def render(self, context):
        return self.html.format(static=settings.STATIC_URL, src=self.src,
                                alt=self.alt)


class ImageFullNode(ImageNode):

    html = u"""
<a href="{static}images-full/{src}" data-lightbox="{name}" data-title="{title}">
    <img src="{static}images/{src}" alt="{alt}">
</a>
"""

    def render(self, context):
        try:
            name = context.dicts[0]['vars']['name']
        except KeyError:  # post.name can be unavailable if file_as_name is set
            name = context.dicts[0]['vars']['title']
        return self.html.format(static=settings.STATIC_URL, src=self.src,
                                alt=self.alt, name=name, title=self.alt)


class ImageBlockNode(template.Node):

    html = u"""
<div class="image-block">
    {block}
</div>"""

    def __init__(self, *image_nodes):
        self.image_nodes = image_nodes

    def render(self, context):
        block = "\n".join(n.render(context) for n in self.image_nodes)
        return self.html.format(block=block)


class ConstNode(template.Node):

    def __init__(self, conststr):
        self.conststr = conststr

    def render(self, context):
        return self.conststr


def image_wrap(parser, token, image_node):
    cont = token.split_contents()
    nodes = []
    alt = src = None
    for val in cont[1:]:
        val = utils.unquote_string(val)
        if val == '|':
            nodes.append(ConstNode("<br>"))
        elif not alt and not src:
            alt = val
        elif alt and not src:
            src = val
            nodes.append(image_node(alt=alt, src=src))
            alt = src = None
    return ImageBlockNode(*nodes)


@register.tag
def image(parser, token):
    return image_wrap(parser, token, ImageNode)


@register.tag
def image_full(parser, token):
    return image_wrap(parser, token, ImageFullNode)


# useful in conjunction with timesince tag: http://stackoverflow.com/a/6481920
@register.filter(is_safe=True)
@stringfilter
def upto(value, delimiter=None):
    return value.split(delimiter)[0]
