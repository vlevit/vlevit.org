from markdown import Markdown
import hashlib
import re
from os import path


def calc_digest(path):
    """
    Return SHA1 string representation of file contents specified by path

    """
    with open(path) as f:
        text = f.read()
        return hashlib.sha1(text).hexdigest()


def name_from_file(relpath):
    """
    Return base name of relpath without extension and with non-word
    characters removed (except '-').

    """
    basename = path.basename(relpath)
    return re.sub('[^\w-]', '-', basename[:basename.rfind('.')])


TAG_RE = re.compile(r'^/(?P<tag>\w+)(:\s*(?P<value>.*(\n[ \t]+\S.*)*))?',
                    re.UNICODE | re.MULTILINE)
TO_ONELINE_RE = re.compile(r'\s*\n\s+', re.UNICODE)


def expand_template_tags(source):
    """
    Replace short tags with django templates tags

    Example:
    /tag: value
    is replaced with
    {% tag "value" %}

    """
    result = []
    pos = 0
    while True:
        m = TAG_RE.search(source, pos)
        if m:
            result.append(source[pos:m.start()])
            tag, value = m.group('tag'), m.group('value')
            if value:
                value, subs = TO_ONELINE_RE.subn(' ', value)
                result.append(u"{{% {} {} %}}".format(tag, value))
            else:
                result.append(u"{{% {} %}}".format(tag))
            pos = m.end()
        else:
            result.append(source[pos:])
            break
    return u''.join(result)


def _attr_list_strict():
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
                                    'codehilite', _attr_list_strict()])
    return markdown.convert(source)
