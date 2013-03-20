from django import forms
from django.contrib.comments.forms import CommentForm
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from threadedcomments.models import ThreadedComment
from threadedcomments.util import safe_markdown


class ThreadedCommentForm(CommentForm):
    _name_title = _('Name (required)')
    _url_title = _('Website')
    _comment_title = _("Enter your comment here...")

    comment = forms.CharField(
        label=_('Comment'),
        widget=forms.Textarea(
            attrs={'title': _comment_title, 'placeholder': _comment_title}),
        max_length=getattr(settings, 'COMMENT_MAX_LENGTH', 3000))
    parent = forms.IntegerField(required=False, widget=forms.HiddenInput)
    name = forms.CharField(
        label=_('Name'), max_length=50,
        widget=forms.TextInput(attrs={'title': _name_title,
                                      'placeholder': _name_title}))
    email = forms.EmailField(label=_('Email address'), required=False)
    url = forms.URLField(
        label=_('Website'), required=False,
        widget=forms.TextInput(attrs={'title': _url_title,
                                      'placeholder': _url_title}))

    def __init__(self, target_object, parent=None, data=None, initial=None):
        self.base_fields.insert(
            self.base_fields.keyOrder.index('comment'), 'title',
            forms.CharField(label=_('Title'), required=False, max_length=getattr(settings, 'COMMENTS_TITLE_MAX_LENGTH', 255))
        )
        self.parent = parent
        if initial is None:
            initial = {}
        initial.update({'parent': self.parent})
        super(ThreadedCommentForm, self).__init__(target_object, data=data, initial=initial)

    def get_comment_model(self):
        return ThreadedComment

    def get_comment_create_data(self):
        d = super(ThreadedCommentForm, self).get_comment_create_data()
        d['parent_id'] = self.cleaned_data['parent']
        d['title'] = self.cleaned_data['title']
        d['comment_html'] = safe_markdown(self.cleaned_data['comment'])
        return d

