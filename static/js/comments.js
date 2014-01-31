/*global $*/

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
    $this.parent().next('.comment_cancel').show();
}

function cancel_reply_form(event) {
    $(this).parent().hide();
    $('#id_parent').val('');
    $('#form-comment').appendTo($('#wrap_write_comment'));
}

var last_comment;

function load_preview() {
    var comment = $('#id_comment').val();
    if (last_comment === comment)
        return;
    if (comment.trim() !== "") {
        $.get($('#comment-form').data('preview'),
              { comment: comment },
              function(data) {
                  $('#comment-preview').fadeIn().html(data);
              });
    } else {
        $('#comment-preview').fadeOut(function(){
            $('#comment-preview').html("");
        });
    }
}


var preview_timeout_id;

function delayed_load_preview() {
    if (preview_timeout_id)
        window.clearTimeout(preview_timeout_id);
    preview_timeout_id = window.setTimeout(load_preview, 1500);
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
                   $('#id_comment').val('');
                   $('#comment-preview').html('').hide();
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
    $(document).on('input', '#id_comment', delayed_load_preview);
    $(document).on('submit', '#comment-form', submit_comment);
});
