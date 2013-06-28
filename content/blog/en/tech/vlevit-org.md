/title: New Home! Moved to vlevit.org
/created: 2013-06-21 10:46:29+03:00
/tags: Django, Python, vlevit.org, wheel

/excerpt: off
*M-x Zeuhl Mode* moved to a new site powered by Django.
/endexcerpt

[TOC]

## Backstory

About two years ago I created a blog on Blogger called [zeuhl-mode]. It was the
blog in Russian on Linux related programs I used or I created for myself. I
liked Blogger more or less — it was easy to start a new blog and it was possible
to paste HTML code in post forms. I used to write posts in [Org mode] and then
used to export them to HTML.

Over time I have discovered a lot of pitfalls in my workflow. I had to
copy+paste code on every post edit, copy+paste titles and tags. I didn't like
Blogger comments and image uploading (since I didn't use web interface for
writing). And I didn't like how Blogger managed themes.

Around the same time I started writing non-tech notes that led me to thinking
about creation of my own site to keep a few blogs in a single place.

[zeuhl-mode]: http://zeuhl-mode.blogspot.com/
[org mode]: http://orgmode.org/

## Static Website Generators: Advantages and Disadvantages

Use of static website generator for my purpose might seem to be a simple and
natural solution. Besides obvious advantages such as low requirements for
hosting and high site speed such solution has nice side effects:

  * everything is stored in plain text
  * it is easy to keep a blog in version control
  * choice of markup language is up to the user
  * site can be viewed locally
  * publication can be as easy as spawning the command (e.g. `git push`)

However static website generators have a significant downside. For obvious
reasons they can't have comments. This problem is usually addressed with
external comments services, like Disqus, which can be embedded to a web page as
JavaScript module. I am not a big fan of such services for technical reasons and
control considerations.

## Development of This Website

I do not find my decision to develop a whole new site from scratch
ill-considered because I find that any existing solution would have required
considerable work to adopt it to my purposes. The main requirement for the site
was to preserve the workflow which is typical for static website generators.

### Workflow

I decided to write the website using [Django] web framework and host it on
[Heroku]. The workflow is the following. Both code and content reside in a single
[git repository]. To publish a blog `git push` is executed which initiates
web site deployment and HTTP POST [hook] triggers importing site to a database.

Unlike most static website generators which usually don't track changes, but
generate all pages from scratch every time they are called, in our case it's
necessary to maintain database state, which requires to track post deletion,
creation, and modification. The code responsible for this is located in
[importers.py]. To speedup site import it is performed only when file changes. A
single file can contain many posts, it's convenient for blog with short posts.

[Django]: https://www.djangoproject.com/
[Heroku]: https://www.heroku.com/
[git repository]: https://github.com/vlevit/vlevit.org/
[hook]: https://addons.heroku.com/deployhooks
[importers.py]: https://github.com/vlevit/vlevit.org/blob/master/vlblog/importers.py

### Markup

[Markdown] is used as markup language. But before Markdown markup is converted
to HTML, it is pre-processed with two additional steps. In the first step the
following string

    /title: New Home! Moved to vlevit.org

is converted to

    {% templatetag openblock %} title New Home! Moved to vlevit.org {% templatetag closeblock %}

and thus, file becomes a valid Django template. In the second step the resulting
template is rendered, and variables like `title` are saved. In the last step
post content is processed with [Markdown][python-markdown]. Such approach allows
to set post title, date, tags, insert images without making sources less
readable. The source of this post can be viewed [here].

[Markdown]: http://daringfireball.net/projects/markdown/syntax
[python-markdown]: http://pythonhosted.org/Markdown/
[here]:  https://github.com/vlevit/vlevit.org/blob/master/content/blog/en/tech/vlevit-org.md

### Comments

Since comments are in fact the only excuse why I don't use static website
generators, they deserved more love. Naturally, the first solution I had a look
at was [django.conrtib.comments]. It appeared that threaded comments are not
supported but the framework is extensible. Then I found extension of Django
comments called [django-threadedcomments]. After some investigation it appeared
that both implementations are not very flexible... Around the same time Django
1.5 was released and in the documentation of Django's development version a
notice appeared saying that django.conrtib.comments is deprecated. And what is
supposed for us to use instead? Disqus... I couldn't accept the fact I had lived
a few days for nothing and implemented comments right atop of
django-threadedcomments.

In my modification comment submission and preview, comment list update and form
validation make use of Ajax requests. Comments can be written in Markdown.
Syntax highlighting is enabled and thanks to [Pygments] a lot of [languages] are
supported. Even [autoit]!

Required fields are only name and comment. I still doesn't completely understand
why almost all comment systems require email. It is usually not verified, thus
it can be invalid, and email subscription if it exists has to be optional and
available for everybody, but not only for those who left a comment. Or is nowadays
email used for a single purpose of displaying avatar from Gravatar?.. While
it remains a mystery for me, I don't collect your emails!

[django.conrtib.comments]: https://docs.djangoproject.com/en/1.5/ref/contrib/comments/
[django-threadedcomments]: https://github.com/HonzaKral/django-threadedcomments
[рекомендуют]: https://docs.djangoproject.com/en/dev/ref/contrib/comments/
[Pygments]: http://pygments.org/
[languages]: http://pygments.org/languages/
[autoit]: http://www.vlevit.org/ru/blog/tech/xatk#c23

#### Importing and Exporting Comments

I pulled out comments from Atom, which Blogger exports to, with regular
expressions and put them to readable [YAML]. Comments are stored in tree-like
structure (recursive list of dictionaries) and comment's content resides there
in Markdown, therefore comments sources are [easy] to read. Import and export
functions are located in [views/comments.py].

[YAML]: http://yaml.org/
[easy]: https://github.com/vlevit/vlevit.org/blob/master/content/blog/ru/tech/comments/xatk.yaml
[views/comments.py]: https://github.com/vlevit/vlevit.org/blob/master/vlblog/views/comments.py

### Website Design

I am a modest person, so design of my website is not pretensions. Some
elements of design were inspired by [distractable.net] and [Redux] theme, the
default Tumblr theme some time ago. The goal of my design was to make it clean
and make big posts readable.

My experiments with web fonts have no result. It is hard to pick up a suitable
font with Latin and Cyrillic glyphs. Also this increases a load size, in
particular if different fonts for headlines and regular text are used. In the
end, I decided to use `sans-serif` almost everywhere with hope that the system
will pick up a readable font.

At first I left font size the default value[^1], relying on that default values
must be reasonable. My system sans serif font is Dejavu Sans, which is much
larger than most other sans serif fonts. That's why I often decrease font size
specially for badly designed sites which break with my font. The default font
size was too big for Dejavu Sans, but my expectation was that it should be more
reasonable in different systems. After a time thanks to [netrender] I found that
I was wrong: 16px sans serif font in Internet Explorer is huge too. I wonder why
modern browsers have such default values? Just for historical reasons? In the
end, I set font size to 14px for blogs with long posts and 13px for blogs with
smaller posts.

The amount of images on this site is as little as possible. At the moment of
writing there are only a few images: favicon, avatar and RSS icon. External widgets
and other tracking elements are not used.

[distractable.net]: http://www.distractable.net/
[Redux]: http://www.tumblr.com/theme/433
[netrender]: http://netrenderer.com/
[^1]: 16px for most browsers

### Deployment

The site is deployed on [Heroku], [PaaS] with Python support. Without doubt
deployment is very convenient, and administration is almost not needed. But it
has downsides too. You don't have control over the environment. Instead you are
supposed to use [add-ons] for such things like data store, caching, logging,
monitoring and other services. Most of add-ons like dynos (containers which
applications run on) has [freemium] business model, which means that some small
amount of functionality is provided for free, but if you want more, you have to
pay. In some way it can explain rather big prices for paid services.

This site uses only free services of Heroku. The main limitation for such small
sites as this one is that dyno falls asleep after hour of inactivity (adding one
more dyno will prevent them from sleeping and will cost 35$/month) and it takes
about 10 seconds to handle the first request which wakes up the dyno. The
limitation can be overcome with periodic pinging of the site. In my case it is
performed by [New Relic] add-on, the monitoring service. Static content is
stored in [Amazon S3] since Heroku doesn't provide a similar service.

[OpenShift], PaaS from Red Hat, is one of alternatives to Heroku. Both Heroku
and OpenShift are functioning on AWS. I find this fact sad. Basically, such PaaS
are functioning only because of different business model.

[Heroku]: https://www.heroku.com/
[PaaS]: http://en.wikipedia.org/wiki/Platform_as_a_service
[add-ons]: https://addons.heroku.com/
[freemium]:http://en.wikipedia.org/wiki/Freemium
[New Relic]: https://addons.heroku.com/newrelic
[Amazon S3]: http://aws.amazon.com/s3/
[OpenShift]: https://www.openshift.com/

### Collecting Statistics

I did not want to use external web services, such as Google Analytics, to
collect requests statistics. And since there is no control over a web server, we
have to collect statistics on Django application level. I use [django-request]
for this purpose. It provides basic statistics for web site requests: traffic
graph, number of requests per page, referrers, browser statistics and few
others. I recommend installing the [version] from GitHub because PyPI contains
the [ancient] version.

Since user requests are processed by Heroku "routers", the application gets the
value of `REMOTE_ADDR` set to IP of such router, which caused my own requests to
affect the results. This issue can be solved by taking into account the value of
`HTTP_X_FORWARDED_FOR`, which Dajngo 1.0 even had special middleware for. I just
[copied] it to my project.

[django-request]: https://django-request.readthedocs.org/
[version]: https://github.com/kylef/django-request
[ancient]: https://pypi.python.org/pypi/django-request/
[copied]: https://github.com/vlevit/vlevit.org/blob/master/middleware/http.py

### Feeds

I learn almost about everything I am interested in from feeds. That's why I
don't like authors' blogs which have their posts cut in feeds. I usually don't
subscribe to them. If you are an author of a such blog, please think twice, how
much you win (or lose) forcing your readers to visit your site.

While there is a rather small amount of posts on the site and traffic is quite
low, all posts are put to feeds. In the future I will probably set some
limit. There are two types of RSS-feeds on posts: a feed for posts from all
blogs:

    http://www.vlevit.org/en/blog.rss

and from the specific blog (e.g. tech)

    http://www.vlevit.org/en/blog/tech.rss

Also there are three types of feeds for comments: a feed for all comments from
all blogs, a feed for all comments from the specific blog (e.g. tech) and a feed
for comments to the specific post (e.g. vlevit-org). Then feed urls will be as
follows (in that order):

    http://www.vlevit.org/en/blog/comments.rss
    http://www.vlevit.org/en/blog/tech/comments.rss
    http://www.vlevit.org/en/blog/tech/vlevit-org/comments.rss

To subscribe to a Russian version of a blog replace `en` with `ru` in the links
above.

## Transferring the Website

All the content of tech blog has been on [zeuhl-mode] up to this post. Half year
ago I transferred zeuhl-mode to a new domain [blog.vlevit.org]. After a time I
will setup a redirection from blog.vlevit.org to [www.vlevit.org] and I will try
to keep all links valid. The old blog will stay on Blogger — I don't like when
people take everything away along with them.

Read and enjoy!<sup id="fnref:†">[†](#fn:†)</sup>

[blog.vlevit.org]: http://blog.vlevit.org/
[www.vlevit.org]: http://www.vlevit.org/
[^†]: And don't read if you don't enjoy!
