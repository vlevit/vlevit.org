/title: key-seq — map pairs of sequentially pressed keys to commands
/created: 2015-06-27 15:53:33+03:00
/tags: Emacs, key-seq, keybindings

/excerpt: off
key-seq is a Emacs package that binds commands to key pairs. It's
similar to key-chord but unlike key-chord key-seq considers the order
of keys, so potentially there are much more "safe" key combinations.
/endexcerpt

So, finally, I'm blogging on Emacs. Over the years I've collected
quite a few Emacs tips worth to share with others. I hope blogging
will make me improve my [.emacs.d] and I'll end up creating a few
packages, so hopefully Emacs community will benefit too. First my post
is dedicated to keybindings, precisely the package called [key-seq].

If you have been interested in ability to run commands inside Emacs
with fewer keys than traditionally long Emacs keybindings require you
must have heard about [key-chord]. If you didn't, briefly, key-chord
allows you to map any two keys to a command. The command will be
executed only if you press keys quickly. It's reasonable to bind the
keys that rarely appear together.

For key-chord it doesn't matter in which order you press keys. For
someone it may sound like a good idea. Though this drastically reduces
the amount of key pairs that are "safe" to use. By "safe" I mean those
key pairs that are almost never appear together in your writings
(texts, code, etc.) For example, in English letter `q` is almost
always followed by `u` (the notable exception for programmers is `ql`
pair as it may stand for "query language"). So for me it sounds
reasonable to use `q` as a prefix. But since key-chord defines key
pairs in both specified order and in reverse, it will also execute
commands for unwanted key pairs.

So the solution is obvious: modify key-chord so it produces only a
single binding. I've used these slightly modified functions for a few
years and now decided to create a package called [key-seq] to simplify
installation for others and submitted it to [MELPA].

If you installed key-chord and key-seq manually than you need load
them first (you can skip this step if you installed both from MELPA or
different package archive):

    :::elisp
    (require 'key-chord)
    (require 'key-seq)

key-seq requires active `key-chord-mode` to work. So first load the
mode globally:

    :::elisp
    (key-chord-mode 1)

Now you can define key pairs as follows:

    :::elisp
    (key-seq-define-global "qd" 'dired)
    (key-seq-define-local "qc" 'compile)
    (key-seq-define text-mode-map "qf" 'flyspell-buffer)

Unset key sequences as follows:

    :::elisp
    (key-seq-unset-global "qd")
    (key-seq-unset-local "qc")
    (key-seq-define text-mode-map "qf" nil)

For customizations use `key-chord-*` variables. For example, you can
slightly increase delays:

    :::elisp
    (setq key-chord-two-keys-delay 0.2)
    (setq key-chord-one-key-delay 0.3)

That's all. Hope you will find this package useful!

---

If you use feeds and you are interested only in my Emacs posts then
you can subscribe to the feed with the following URL:

    http://vlevit.org/en/blog/tech/tag/Emacs.rss


[.emacs.d]: https://github.com/vlevit/.emacs.d
[key-seq]: https://github.com/vlevit/key-seq.el
[key-chord]: http://www.emacswiki.org/emacs/key-chord.el
[MELPA]: http://melpa.org/#/key-seq
