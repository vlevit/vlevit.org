/*global $*/

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
    var comment = $('#id_comment').val();
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
    var $this = $(this);
    $.post($this.attr('action').replace("removethis", ""),
           $this.serialize(),
           function(data) {
               var $data = $($.trim(data));
               if ( $data.is('div.comments') ) {
                   // restore comment form initial state
                   $('#form-comment').appendTo($('#wrap_write_comment'));
                   ensure_comment_form_visible();
                   $('#id_comment').val('');
                   $('#comment-error').hide();

                   // update comment list
                   $('div.comments').html($data.html());

               } else if ( $data.is('div.comment-error') ) {
                   // form validation failed, display errors
                   var $error = $('#comment-error');
                   $error.html($data.html());
                   $error.show();
               }
           }).fail(function() { alert("error"); });
    return false;
}

$.fn.ready(function() {
    $(document).on('click', '.comment_reply_link', show_reply_form);
    $(document).on('click', '.cancel_reply', cancel_reply_form);
    $(document).on('click', '#preview-link', load_preview);
    $(document).on('click', '#preview-cancel', cancel_preview);
    $(document).on('submit', '#comment-form', submit_comment);
});
