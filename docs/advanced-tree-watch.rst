.. Included in advanced.rst

Introduction
^^^^^^^^^^^^

As mentioned in :ref:`QueueManager`, commands configured to be
executed during item loading can be templates. This can be used to
support all sorts of tricks, the most common ones are explained here,
including fully dynamic completion moving. If the following explanation
of the inner workings is too technical and nerdy for you, skip to the
:ref:`tree-watch-examples` section below, and just adapt one of the
prepared use cases to your setup.

So how does this work? When a ``.torrent`` file is notified for loading via ``inotify``,
it's parsed and contained data is put into variables that can be used in
the command templates. In order to get an idea what variables are
available, you can dump the templating namespace for a metafile to the
console, by calling the ``watch`` job directly.

Consider this example:

.. code-block:: shell

    $ date >example.dat
    $ mktor -q example.dat http://tracker.example.com/
    $ python-pyrocore -m pyrocore.torrent.watch -v example.dat.torrent
    …
    DEBUG    Tree watcher created with config Bunch(active=False, …
        cmd.target='{{# set target path\n}}d.custom.set=targetdir,/var/torrent/done/{{label}}/{{relpath}}',
        dry_run=True, handler='pyrocore.torrent.watch:TreeWatch', job_name='treewatch',
        load_mode='start', path='/var/torrent', queued='True', quiet='False', schedule='hour=*')
    DEBUG    custom commands = {'target': <Template 2d01990 name=None>, 'nfo': f.multicall=*.nfo,f.set_priority=2, …}
    INFO     Templating values are:
        commands=[…, 'd.custom.set=targetdir,/var/torrent/done//pyrocore', …]
        filetype='.dat'
        …
        info_hash='8D59E3FD8E78CC9896BDE4D65B0DC9BDBA0ADC70'
        info_name='example.dat'
        label=''
        pathname='/var/torrent/pyroscope/example.dat.torrent'
        relpath='pyrocore'
        tracker_alias='tracker.example.com'
        traits=Bunch(kind=None)
        watch_path=set(['/var/torrent'])


Things to take note of:

#. the ``target`` custom command is expanded to set the ``targetdir``
   rTorrent attribute to the completion path (which can then be used
   in a typical ``event.download.finished`` handler),
   using the ``relpath`` variable which is obtained from the full
   ``.torrent`` path, relative to the watch dir root.
#. all kinds of other information is made available, like the torrent's
   info hash and the tracker alias; thus you can write conditional templates
   based on tracker, or use the tracker name in a completion path.
#. for certain types of downloads, ``traits`` provides parsed information to
   build specific target paths, e.g. for the ``Pioneer.One.S01E06.720p.x264-VODO``
   TV episode, you'll get this:

   .. code-block:: ini

      label='tv/mkv'
      traits=Bunch(aspect=None, codec='x264', episode='06', extension=None, format='720p',
          group='VODO', kind='tv', pattern='Normal TV Episodes', release=None,
          release_tags=None, season='01', show='Pioneer.One', sound=None, title=None)


.. _tree-watch-examples:

Tree Watch Examples
^^^^^^^^^^^^^^^^^^^

.. contents::
    :local:


Completion Moving
"""""""""""""""""

Since the templating namespace automatically includes the path of a
loaded ``.torrent`` file relative to the watch root (in ``relpath``, see
above example namespace output and the config example further down), you
can set the "move on completion" target using that value.

.. code-block:: ini

    job.treewatch.cmd.target    = {{# set target path
        }}d.custom.set=targetdir,/var/torrent/done/{{label}}/{{relpath}}

Note that this still needs a typical completion event handler that takes
the custom variable that is set, and moves the data based on its value.


Tree Watch with Sorting
"""""""""""""""""""""""

This example adds a *second* job for a ``sorted`` tree that directly saves
the data into a path based on the loaded metafile's location.

.. code-block:: ini

    # Tree watch with location
    job.watch-sorted.handler        = pyrocore.torrent.watch:TreeWatch
    job.watch-sorted.schedule       = hour=*
    job.watch-sorted.active         = True

    job.watch-sorted.load_mode      = normal
    job.watch-sorted.queued         = True
    job.watch-sorted.path           = /var/torrent/sorted/watch
    job.watch-sorted.cmd.setdir     = {{# set download path
        }}{{if '/music/' in pathname}}{{# add metafile basename to path
            }}d.directory_base.set="/var/torrent/sorted/{{relpath}}/{{pathname|h.pathname}}"{{#
        }}{{elif traits.kind == 'tv'}}{{# store TV content into separate show folders
            }}d.directory.set="/var/torrent/sorted/{{relpath}}/{{traits.get('show', '_UNKNOWN').replace('.',' ').title()}}"{{#
        }}{{else}}{{# just use the relative metafile location
            }}d.directory.set="/var/torrent/sorted/{{relpath}}"{{#
        }}{{endif}}

Change the values in the second block to suit your needs. As given,
an item loaded from ``…/sorted/watch/movies/*.torrent``
would end up in the ``…/sorted/movies`` directorey
(with the filename coming from inside the metafile as usual),
and it won't start by itself.

Also, paths containing ``music`` use the metafile's basename as the data directory,
and metafiles recognized as TV content get separated into show directories.
