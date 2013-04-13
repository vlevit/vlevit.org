import logging

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.dateparse import parse_datetime

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


# useful in conjunction with timesince tag: http://stackoverflow.com/a/6481920
@register.filter(is_safe=True)
@stringfilter
def upto(value, delimiter=None):
    return value.split(delimiter)[0]
