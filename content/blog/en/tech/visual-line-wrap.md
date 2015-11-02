/title: Visual Line Wrapping in Emacs
/created: 2015-09-29 01:37:36+03:00
/published: 2015-11-03 00:37:54+02:00
/tags: Emacs, mu4e

/excerpt

In this blog post I will explain how to edit unwrapped text in Emacs
like if it was hard-wrapped. Also I'll share the related configuration
for whitespace-mode and mu4e.

/endexcerpt

If you are using plain text regularly probably you prefer wrapping
text with hard breaks. Hard wrapping ensures that text remains
readable regardless how large the window size is. But there are cases
when soft wrapping is desirable. For example, you may want it when
viewing text with no hard breaks (say, in emails you received). Other
examples are services like GitHub which expect emails to be softly
wrapped and web forms which usually don't work well with hard-wrapped
input. The issue here is that in the text editor to keep the text
readable we probably need to soft-wrap at fixed column instead of
window edge. This way we would be able to edit text as it were
hard-wrapped.

To achieve this in Emacs there is a built-in mode called
`visual-line-mode`. It redefines the commands so they apply to visual
lines instead of hard lines. But the mode doesn't provide a way to
wrap text on the specific column. That is what [visual-fill-column] is
for. `visual-fill-column-mode` wraps text softly and considers the
`fill-column` variable. So with both these modes activated we can work
with softly wrapped text the same way as with hard-wrapped one.

[visual-fill-column]: https://github.com/joostkremers/visual-fill-column

Now you would probably like to see some indication of whether
paragraph is hard- or soft-wrapped. You can show fringes for visual
lines as such

    :::elisp
    (setq visual-line-fringe-indicators '(left-curly-arrow right-curly-arrow))

Though I prefer using `whitespace-mode` to display hard newlines. If I
were writing this blog post with no hard breaks in paragraphs it would
look like this (notice the symbol `↷` at the line endings):

/image_full: "showing newlines with whitespace-mode" tech/emacs/whitespace-newlines.png

My `whitespace-mode` setup responsible for showing `↷` indicators is
the following:

    :::elisp
    (setq whitespace-display-mappings
        '((newline-mark 10 [?↷ 10])))      ; newline

    (eval-after-load 'whitespace
      (lambda ()
        (set-face-attribute 'whitespace-newline nil :foreground "#d3d7cf")))

I'm activating the `whitespace-mode` alongside with
`visual-fill-column-mode` in `visual-line-mode` hook as follows:

    :::elisp
    (defvar my-visual-line-state nil)

    (defun my-visual-line-mode-hook ()
      (when visual-line-mode
        (setq my-visual-line-state
              `(whitespace-style ,whitespace-style
                whitespace-mode ,whitespace-mode
                auto-fill-mode ,auto-fill-function))

        (when whitespace-mode
          whitespace-mode -1)

        ;; display newline characters with whitespace-mode
        (make-local-variable 'whitespace-style)
        (setq whitespace-style '(newline newline-mark))
        (whitespace-mode)

        ;; disable auto-fill-mode
        (when auto-fill-function
          (auto-fill-mode -1))

        ;; visually wrap text at fill-column
        (visual-fill-column-mode)))

    (add-hook 'visual-line-mode-hook 'my-visual-line-mode-hook)

Now to exit `visual-line-mode` we need to disable all the modes we
activated and revert the settings we modified. So I have a dedicated
function to disable `visual-line-mode`:

    :::elisp
    (defun my-visual-line-mode-off ()
      (interactive)
      (visual-fill-column-mode--disable)
      (visual-line-mode -1)
      ;; revert the state before activating visual-line-mode
      (when my-visual-line-state
        (let ((ws-style (plist-get my-visual-line-state 'whitespace-style))
              (ws-mode (plist-get my-visual-line-state 'whitespace-mode))
              (af-mode (plist-get my-visual-line-state 'auto-fill-mode)))

          (when whitespace-mode
            (whitespace-mode -1))
          (when ws-style (setq whitespace-style ws-style))
          (when ws-mode (whitespace-mode 1))

          (when af-mode (auto-fill-mode 1)))))

If I want to toggle `visual-line-mode` I call the following function:

    :::elisp
    (defun my-visual-line-mode-toggle ()
      (interactive)
      (if visual-line-mode
          (my-visual-line-mode-off)
        (visual-line-mode 1)))

Finally, I mapped the visual line mode toggling to the key sequence
`qm` (see [key-seq]):

    :::elisp
    (key-seq-define-global "qm" 'my-visual-line-mode-toggle)

[key-seq]: /en/blog/tech/key-seq

If you're using email inside Emacs you may also want to activate
`visual-line-mode` in the mode displaying emails (many promotional and
transactional emails don't use hard wrap). For `mu4e` I'm just
registering `visual-line-mode` on `mu4e-view-mode`'s hook:

    :::elisp
    (add-hook 'mu4e-view-mode-hook 'visual-line-mode)

When replying to GitHub (and similar) emails I'm activating
`visual-line-mode` for the new email via the following hook:

    :::elisp
    (add-hook 'mu4e-compose-mode-hook
      (defun my-mu4e-visual-line-reply ()
        "Activate visual-line-mode for specific services like GitHub."
        (let ((msg mu4e-compose-parent-message))
          (when (and msg (mu4e-message-contact-field-matches
                          msg :from '(".*@github.com$" ".*@upwork.com$")))
            (visual-line-mode)))))

Whenever I want to toggle the `visual-line-mode` manually I press
`qm`. If needed I adjust `fill-column` before that.

You can find my [emacs.d] setup on GitHub:

 * [setup-visual-line.el]
 * [setup-whitespace.el]
 * [setup-mu4e.el]

[emacs.d]: https://github.com/vlevit/.emacs.d/
[setup-visual-line.el]: https://github.com/vlevit/.emacs.d/blob/master/setup-lisp/setup-visual-line.el
[setup-whitespace.el]: https://github.com/vlevit/.emacs.d/blob/master/setup-lisp/setup-whitespace.el
[setup-mu4e.el]: https://github.com/vlevit/.emacs.d/blob/master/setup-lisp/setup-mu4e.el#L97
