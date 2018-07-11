.. copied from https://bitbucket.org/ianb/tempita
.. The old docs URL is defunct, including the Wayback redirect

Tempita Templating Engine
=========================

:author: Ian Bicking <ianb@colorstudy.com>
:source: https://bitbucket.org/ianb/tempita


Status & License
----------------

Tempita is available under a `MIT-style license`.

It is *not* actually actively developed, and not an ambitious project.  It does not
seek to take over the templating world, or adopt many new features.
I just wanted a small templating language for cases when ``%`` and
``string.Template`` weren't enough.


Why Another Templating Language
-------------------------------

Surely the world has enough templating languages?  So why did I write
another.

I initially used `Cheetah <http://cheetahtemplate.org/>`_ as the
templating language for `Paste Script
<http://pythonpaste.org/script/>`_, but this caused quite a few
problems.  People frequently had problems installing Cheetah because
it includes a C extension.  Also, the errors and invocation can be a
little confusing.  This might be okay for something that used
Cheetah's features extensively, except that the templating was a very
minor feature of the system, and many people didn't even understand or
care about where templating came into the system.

At the same time, I was starting to create reusable WSGI components
that had some templating in them.  Not a lot of templating, but enough
that ``string.Template`` had become too complicated -- I need if
statements and loops.

Given this, I started looking around for a very small templating
language, and I didn't like anything I found.  Many of them seemed
awkward or like toys that were more about the novelty of the
implementation than the utility of the language.

So one night when I felt like coding but didn't feel like working on
anything I was already working on, I wrote this.  It was first called
``paste.util.template``, but I decided it deserved a life of its own,
hence Tempita.


The Interface
-------------

The interface is intended to look a lot like ``string.Template``.  You
can create a template object like::

    >>> import tempita
    >>> tmpl = tempita.Template("""Hello {{name}}""")
    >>> tmpl.substitute(name='Bob')
    'Hello Bob'

Or if you want to skip the class::

    >>> tempita.sub("Hello {{name}}", name='Alice')
    'Hello Alice'

Note that the language allows arbitrary Python to be executed, so
your templates must be trusted.

You can give a name to your template, which is handy when there is an
error (the name will be displayed)::

    >>> tmpl = tempita.Template('Hi {{name}}', name='tmpl')
    >>> tmpl.substitute()
    Traceback (most recent call last):
        ...
    NameError: name 'name' is not defined at line 1 column 6 in file tmpl

You can also give a namespace to use by default, which
``.substitute(...)`` will augment::

    >>> tmpl = tempita.Template(
    ...     'Hi {{upper(name)}}',
    ...     namespace=dict(upper=lambda s: s.upper()))
    >>> tmpl.substitute(name='Joe')
    'Hi JOE'

Lastly, you can give a dictionary-like object as the argument to
``.substitute``, like::

    >>> name = 'Jane'
    >>> tmpl.substitute(locals())
    'Hi JANE'

There's also an `HTMLTemplate`_ class that is more appropriate for
templates that produce HTML.

You can also instantiate a template from a filename with
``Template.from_filename(filename, namespace={}, encoding=None)``.
This is like calling::

    Template(open(filename, 'rb').read().decode(encoding),
             name=filename, namespace=namespace)


Unicode
-------

Tempita tries to handle unicode gracefully, for some value of
"graceful".  ``Template`` objects have a ``default_encoding``
attribute.  It will try to use that encoding whenever ``unicode`` and
``str`` objects are mixed in the template.  E.g.::

    >>> tmpl = tempita.Template(u'Hi {{name}}')
    >>> import sys
    >>> if sys.version.startswith('2'): # unicode is the default in 3 -> failing test
    ...     val = tmpl.substitute(name='Jos\xc3\xa9')
    ...     comparison = val == u'Hi Jos\xe9'
    ... else:
    ...     comparison = True
    >>> comparison
    True
    >>> tmpl = tempita.Template('Hi {{name}}')
    >>> print (tmpl.substitute(name=u'Jos\xe9'))
    Hi José

The default encoding is UTF8.


.. _tempita-lang:

The `Tempita` Language
----------------------

The language is fairly simple; all the constructs look like
``{{stuff}}``.

Substitution
^^^^^^^^^^^^

To insert a variable or expression, use ``{{expression}}``.  You can't
use ``}}`` in your expression, but if it comes up just use ``} }``
(put a space between them).  You can pass your expression through
*filters* with ``{{expression | filter}}``, for instance
``{{expression | repr}}``.  This is entirely equivalent to
``{{repr(expression)}}``.  But it might look nicer to some people; I
took it from Django because I liked it.  There's a shared namespace,
so ``repr`` is just an object in the namespace.

If you want to have ``{{`` or ``}}`` in your template, you must use
the built-in variables like ``{{start_braces}}`` and
``{{end_braces}}``.  There's no escape character.

You may also specify the delimiters as an argument to the Template
__init__ method:

    >>> tempita.Template(content='Hello ${name}', delimiters=('${', '}')).substitute(name='world')
    'Hello world'

The delimiters argument must be of length two and both items must be strings.

None, as a special case, is substituted as the empty string.

Also there is a command for setting default values in your template::

    {{default width = 100}}

You can use this so that the ``width`` variable will always have a
value in your template (the number ``100``).  If someone calls
``tmpl.substitute(width=200)`` then this will have no effect; only if
the variable is undefined will this default matter.  You can use any
expression to the right of the ``=``.

if
^^

You can do an if statement with::

    {{if condition}}
      true stuff
    {{elif other_condition}}
      other stuff
    {{else}}
      final stuff
    {{endif}}

Some of the blank lines will be removed when, as in this case, they
only contain a single directive.  A trailing ``:`` is optional (like
``{{if condition:}}``).


for
^^^

Loops should be unsurprising::

    {{for a, b in items}}
        {{a}} = {{b | repr}}
    {{endfor}}

See?  Unsurprising.  Note that nested tuples (like ``for a, (b, c)
in...``) are not supported (patches welcome).


inherit & def
^^^^^^^^^^^^^

You can do template inheritance.  To inherit from another template
do::

    {{inherit "some_other_file"}}

From Python you must also pass in, to `Template`, a `get_template`
function; the implementation for ``Template.from_filename(...)`` is::

    def get_file_template(name, from_template):
        path = os.path.join(os.path.dirname(from_template.name), name)
        return from_template.__class__.from_filename(
            path, namespace=from_template.namespace,
            get_template=from_template.get_template)

You can also pass in a constructor argument `default_inherit`, which
will be the inherited template name when no ``{{inherit}}`` is in the
template.

The inherited template is executed with a variable ``self``, which
includes ``self.body`` which is the text of the child template.  You
can also put in definitions in the child, like::

    {{def sidebar}}
      sidebar links...
    {{enddef}}

Then in the parent/inherited template::

    {{self.sidebar}}

If you want to make the sidebar method optional, in the inherited
template use::

    {{self.get.sidebar}}

If ``sidebar`` is not defined then this will just result in an object
that shows up as the empty string (but is also callable).

This can be called like ``self.sidebar`` or ``self.sidebar()`` -- defs
can have arguments (like ``{{def sidebar(name)}}``), but when there
are no arguments you can leave off ``()`` (in the call and
definition).


Python blocks
^^^^^^^^^^^^^

For anything more complicated, you can use blocks of Python code,
like::

    {{py:x = 1}}

    {{py:
    lots of code
    }}

The first form allows statements, like an assignment or raising an
exception.  The second form is for multiple lines.  If you have
multiple lines, then ``{{py:`` must be on a line of its own and the
code can't start out indented (but if you have something like ``def
x():`` you would indent the body).

These blocks of code can't output any values, but they can calculate
values and define functions.  So you can do something like::

    {{py:
    def pad(s):
        return s + ' '*(20-len(s))
    }}
    {{for name, value in kw.items()}}
    {{s | pad}} {{value | repr}}
    {{endfor}}

As a last detail ``{{# comments...}}`` doesn't do anything at all,
because it is a comment.


bunch and looper
^^^^^^^^^^^^^^^^

There's two kinds of objects provided to help you in your templates.
The first is ``tempita.bunch``, which is just a dictionary that also
lets you use attributes::

    >>> bunch = tempita.bunch(a=1)
    >>> bunch.a
    1
    >>> list(bunch.items())
    [('a', 1)]
    >>> bunch.default = None
    >>> print (bunch.b)
    None

This can be nice for passing options into a template.

The other object is for use inside the template, and is part of the
default namespace, ``looper``.  This can be used in ``for`` loops in
some convenient ways.  You basically use it like::

    {{for loop, item in looper(seq)}}
      ...
    {{endfor}}

The ``loop`` object has a bunch of useful methods and attributes:

    ``.index``
      The index of the current item (like you'd get with
      ``enumerate()``)
    ``.number``
      The number: ``.index + 1``
    ``.item``
      The item you are looking at.  Which you probably already have,
      but it's there if you want it.
    ``.next``
      The next item in the sequence, or None if it's the last item.
    ``.previous``
      The previous item in the sequence, or None if it's the first
      item.
    ``.odd``
      True if this is an odd item.  The first item is even.
    ``.even``
      True if it's even.
    ``.first``
      True if this is the first item.
    ``.last``
      True if this is the last item.
    ``.length``
      The total length of the sequence.
    ``.first_group(getter=None)``
      Returns true if this item is the first in the group, where the
      group is either of equal objects (probably boring), or when you
      give a getter.  getter can be ``'.attribute'``, like
      ``'.last_name'`` -- this lets you group people by their last
      name.  Or a method, like ``'.birth_year()'`` -- which calls the
      method.  If it's just a string, it is expected to be a key in a
      dictionary, like ``'name'`` which groups on ``item['name']``.
      Or you can give a function which returns the value to group on.
      This always returns true when ``.first`` returns true.
    ``.last_group(getter=None)``
      Like ``first_group``, only returns True when it's the last of
      the group.  This always returns true when ``.last`` returns true.

Note that there's currently a limitation in the templating language,
so you can't do ``{{for loop, (key, value) in looper(d.items())}}``.
You'll have to do::

    {{for loop, key_value in looper(d.items())}}
      {{py:key, value = key_value}}
      ...
    {{endfor}}


HTMLTemplate
------------

In addition to ``Template`` there is a template specialized for HTML,
``HTMLTemplate`` (and the substitution function ``sub_html``).

The basic thing that it adds is automatic HTML quoting.  All values
substituted into your template will be quoted unless they are
specially marked.

You mark objects as instances of ``tempita.html``.  The easiest way is
``{{some_string | html}}``, though you can also use
``tempita.html(string)`` in your functions.

An example::

    >>> tmpl = tempita.HTMLTemplate('''\
    ... Hi {{name}}!
    ... <a href="{{href}}">{{title|html}}</a>''')
    >>> name = tempita.html('<img src="bob.jpg">')
    >>> href = 'Attack!">'
    >>> title = '<i>Homepage</i>'
    >>> tmpl.substitute(locals())
    'Hi <img src="bob.jpg">!\n<a href="Attack!&quot;&gt;"><i>Homepage</i></a>'

It also adds a couple handy builtins:

    ``html_quote(value)``:
        HTML quotes the value.  Turns all unicode values into
        character references, so it always returns ASCII text.  Also
        it calls ``str(value)`` or ``unicode(value)``, so you can do
        things like ``html_quote(1)``.

    ``url(value)``:
        Does URL quoting, similar to ``html_quote()``.

    ``attr(**kw)``:
        Inserts attributes.  Use like::

            <div {{attr(width=width, class_=div_class)}}>

        Then it'll put in something like ``width="{{width}}"
        class={{div_class}}``.  Any attribute with a value of None is
        left out entirely.


Extending Tempita
-----------------

It's not really meant for extension.  Instead you should just write
Python functions and classes that do what you want, and use them in
the template.  You can either add the namespace to the constructor, or
extend ``default_namespace`` in your own subclass.

The extension that ``HTMLTemplate`` uses is to subclass and override
the ``_repr(value, pos)`` function.  This is called on each object
just before inserting it in the template.

Two other methods you might want to look at are ``_eval(code, ns,
pos)`` and ``_exec(code, ns, pos)``, which evaluate and execute
expressions and statements.  You could probably make this language
safe with appropriate implementations of those methods.


Command-line Use
----------------

There's also a command-line version of the program.  In Python 2.5+
you can run ``python -m tempita``; in previous versions you must run
``python path/to/tempita/__init__.py``.

The usage::

    Usage: __init__.py [OPTIONS] TEMPLATE arg=value

    Use py:arg=value to set a Python value; otherwise all values are
    strings.


    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -o FILENAME, --output=FILENAME
                            File to write output to (default stdout)
      --html                Use HTML style filling (including automatic HTML
                            quoting)
      --env                 Put the environment in as top-level variables

So you can use it like::

    $ python -m tempita --html mytemplate.tmpl \
    >     var1="$var1" var2="$var2" > mytemplate.html


Still To Do
-----------

* Currently nested structures in ``for`` loop assignments don't work,
  like ``for (a, b), c in x``.  They should.

* There's no way to handle exceptions, except in your ``py:`` code.
  I'm not sure what there should be, if anything.

* Probably I should try to dedent ``py:`` code.

* There should be some way of calling a function with a chunk of the
  template.  Maybe like::

    {{call expr}}
      template code...
    {{endcall}}

  That would mean ``{{expr(result_of_template_code)}}``.  But maybe
  there should be another assignment form too, if you don't want to
  immediately put the output in the code (``{{x =
  call}}...{{endcall}}?``).  For now defs could be used for this,
  like::

    {{def something}}
      template code...
    {{enddef}}
    {{expr(something())}}

News
----

0.5
^^^

* Python 3 compatible.

* Fixed bug where file-relative filenames wouldn't work well.

* Fixed the stripping of empty lines.

0.4
^^^

* Added a ``line_offset`` constructor argument, which can be used to
  adjust the line numbers reported in error messages (e.g., if a
  template is embedded in a file).

* Allow non-dictionary namespace objects (with
  ``tmpl.substitute(namespace)`` (in Python 2.5+).

* Instead of defining ``__name__`` in template namespaces (which has special
  rules, and must be a module name) the template name is put into
  ``__template_name__``.  This became important in Python 2.5.

* Fix some issues with \r

0.3
^^^

* Added ``{{inherit}}`` and ``{{def}}`` for doing template inheritance.

* Make error message annotation slightly more robust.

* Fix whitespace stripping for the beginning and end of lines.

0.2
^^^

* Added ``html_quote`` to default functions provided in
  ``HTMLTemplate``.

* HTML literals have an ``.__html__()`` method, and the presence of
  that method is used to determine if values need to be quoted in
  ``HTMLTemplate``.
