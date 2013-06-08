import logging

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.dateparse import parse_datetime

import utils


logger = logging.getLogger(__name__)


register = template.Library()


@register.simple_tag(takes_context=True)
def title(context, value):
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['title'] = value
    return u''


@register.simple_tag(takes_context=True)
def created(context, value):
    try:
        dt = parse_datetime(value)
    except ValueError:
        dt = None
    if not dt:
        logger.warning('in template: invalid date: %s', value)
        return u''
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['created'] = dt
    return u''


@register.simple_tag(takes_context=True)
def tags(context, value):
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['tags'] = map(
        lambda s: s.strip(), value.split(','))
    return u''


@register.simple_tag(takes_context=True)
def name(context, value):
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['name'] = value
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
        show = cont[1][1:-1]
    nodelist = parser.parse(('endexcerpt', ))
    parser.delete_first_token()
    return ExcerptNode(nodelist, show)


IMAGE_BLOCK = u"""
<div class="image-block">
    {block}
</div>"""


IMAGE_HTML = u"""<img src="{static}images/{src}" alt="{alt}"></img>"""


IMAGE_FULL_HTML = u"""
<a href="{static}images-full/{src}">
    <img src="{static}images/{src}" alt="{alt}"></img>
</a>
"""


class ImageNode(template.Node):

    def __init__(self, image_html):
        self.image_html = image_html

    def render(self, context):
        return self.image_html


def image_wrap(parser, token, html):
    cont = token.split_contents()
    output = []
    alt = src = None
    for val in cont[1:]:
        val = utils.unquote_string(val)
        if val == '|':
            output.append("<br>")
        elif not alt and not src:
            alt = val
        elif alt and not src:
            src = val
            static = settings.STATIC_URL
            img = html.format(static=static, alt=alt, src=src)
            output.append(img)
            alt = src = None
    image_html = '\n'.join(output)
    image_html = IMAGE_BLOCK.format(block=image_html)
    return ImageNode(image_html)


@register.tag
def image(parser, token):
    return image_wrap(parser, token, IMAGE_HTML)


@register.tag
def image_full(parser, token):
    return image_wrap(parser, token, IMAGE_FULL_HTML)


# useful in conjunction with timesince tag: http://stackoverflow.com/a/6481920
@register.filter(is_safe=True)
@stringfilter
def upto(value, delimiter=None):
    return value.split(delimiter)[0]
