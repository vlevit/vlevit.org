function ensure_preview_visible() {
    $('#comment-comment').hide();
    $('#comment-preview').show();
    $('#preview-link').hide();
    $('#preview-cancel').show();
}

function ensure_comment_form_visible() {
    $('#comment-preview').hide();
    $('#comment-comment').show();
    $('#preview-cancel').hide();
    $('#preview-link').show();
}

function hide_last_cancel_reply() {
    var last_parent_id = $('#id_parent').val();
    if ( last_parent_id !== '' ) {
        $('#c' + last_parent_id + ' .comment_cancel').hide();
    }
}

function show_reply_form(event) {
    var $this = $(this);
    var comment_id = $this.data('comment-id');

    hide_last_cancel_reply();
    $('#id_parent').val(comment_id);
    $('#form-comment').insertAfter($this.closest('.comment'));
    ensure_comment_form_visible();
    $this.parent().next('.comment_cancel').show();
}

function cancel_reply_form(event) {
    $(this).parent().hide();
    $('#id_parent').val('');
    $('#form-comment').appendTo($('#wrap_write_comment'));
    ensure_comment_form_visible();
}

function load_preview(event) {
    comment = $('#id_comment').val();
    if (comment.trim() !== "") {
        $.get($('#preview-link a:first').attr('href'),
              { comment: comment },
              function(data) {
                  $('#comment-preview').html(data);
                  ensure_preview_visible();
              });
    }
    return false;
}

function cancel_preview(event) {
    ensure_comment_form_visible();
    return false;
}

function submit_comment(event) {
    $this = $(this);
    $.post($this.attr('action'),
           $this.serialize(),
           function(data) {
               $data = $($.trim(data));
               if ( $data.is('div.comments') ) {
                   // restore comment form initial state
                   $('#form-comment').appendTo($('#wrap_write_comment'));
                   ensure_comment_form_visible();
                   $('#id_comment').val('');
                   $('#comment-error').hide();

                   // update comment list
                   $('div.comments').html($data.html());

                   // rebind events for links in comment list
                   register_comment_list_events();
               } else if ( $data.is('div.comment-error') ) {
                   // form validation failed, display errors
                   $error = $('#comment-error');
                   $error.html($data.html());
                   $error.show();
               }
           }).fail(function() { alert("error"); });
    return false;
}

function register_comment_list_events() {
    $('.comment_reply_link').click(show_reply_form);
    $('.cancel_reply').click(cancel_reply_form);
    $('#preview-link').click(load_preview);
    $('#preview-cancel').click(cancel_preview);
}

$.fn.ready(function() {
    register_comment_list_events();
    $('#comment-form').submit(submit_comment);
})
