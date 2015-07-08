/title: xatk 0.2 — still a window switcher for X11
/created: 2015-07-09 00:07:14+03:00
/tags: xatk, windows, keys, wheel, x11

/excerpt: on

Eventually I've released a new version of xatk — xatk 0.2. It wasn't
getting updates almost for 3 years. But it's not because of lack of
interest. I'm using it for 5 years now and I'm kind of addicted to it.
When it stops working I feel very confused. So you may think xatk was
stable enough for all those years. Almost. There have been only a few
crashes for this period, but they all must have been fixed in 0.2.

/endexcerpt

[TOC]

[GitHub]: https://github.com/vlevit/xatk
[Read the Docs]: http://xatk.readthedocs.org/en/latest/

The most visible change is that xatk has moved to [GitHub] since
Google Code is shutting down and consequently it moved from Mercurial
to Git. The documentation is now hosted on [Read the Docs]. Aside from
these changes there are a few new features (actually two of them were
implemented in 2012 but the didn't get into any release).

The first and the most interesting new feature is the ability to run
the program if it has no open windows. It's also known as run or
raise. The feature works only for windows you specified in the
configuration, not all windows (otherwise it would messy). Programs to
run are specified in `[RULES]` section of `~/.xatk/xatkrc`. For
example,

    class.emacs = !e = emacs

specifies to bind all Emacs windows (windows with class `emacs`) to
shortcut `e` and if there is no Emacs window then run command `emacs`.
Commands are executed by your default shell so you can use shell
constructs here like setting environment variables (before the
command) or stream redirection operators.

Other new features are a new xatk option `xatk --kill` which stops
xatk gracefully and a an implementation of xatk locking so only one
instance can be run (If you ran a few xatk < 0.2 instances they would
spam window titles indefinitely).

The last improvement is a set of bug fixes which I hope will make xatk
even more stable. And if it doesn't I promise I will not wait another
3 years to make a new release;-)
