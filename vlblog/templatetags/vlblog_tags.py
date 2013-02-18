from django import template
from django.utils.dateparse import parse_datetime
import logging


logger = logging.getLogger(__name__)


register = template.Library()


@register.simple_tag(takes_context=True, name='title')
def title(context, value):
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['title'] = value
    return u''


@register.simple_tag(takes_context=True)
def date(context, value):
    try:
        dt = parse_datetime(value)
    except ValueError:
        dt = None
    if not dt:
        logger.warning('in template: invalid date: %s', value)
        return u''
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['date'] = dt
    return u''


@register.simple_tag(takes_context=True)
def tags(context, value):
    if 'vars' not in context.dicts[0]:
        context.dicts[0]['vars'] = {}
    context.dicts[0]['vars']['tags'] = map(
        lambda s: s.strip(), value.split(','))
    return u''


class ExcerptNode(template.Node):

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        logger.debug('FieldNode render')
        excerpt = self.nodelist.render(context)
        if 'vars' not in context.dicts[0]:
            context.dicts[0]['vars'] = {}
        context.dicts[0]['vars']['excerpt'] = excerpt
        return excerpt


@register.tag
def excerpt(parser, token):
    # return FieldNode(token.split_contents()[1:])
    nodelist = parser.parse(('endexcerpt', ))
    parser.delete_first_token()
    return ExcerptNode(nodelist)
