plone.backup
************

Easy backup and restore of a Plone (or Zope) ZODB filestorage and blobstorage.

.. contents::


Introduction
------------

``plone.backup`` is a wrapper around ``repozo``, the ZODB backup tool.
Looking up the settings for ``repozo`` and backing up the blobstorage is a chore,
and you have to pick a directory where to put the backups.
This package provides **sensible defaults** for your common backup tasks.

This is the standalone successor of the zc.buildout recipe
`collective.recipe.backup <https://pypi.org/project/collective.recipe.backup/>`_.
It has the same features, the same options, and the same commands,
but it does not need buildout.
It is meant for projects created with `cookieplone <https://github.com/plone/cookieplone>`_,
and for Docker based deployments.

The options are environment variables, for example ``PLONE_BACKUP_KEEP=3``.
So you can configure it with a ``.env`` file in your project,
or with the ``environment`` of a container.

These are the commands:

- ``backup`` makes an incremental backup.

- ``restore`` restores the latest backup created by the backup command.

- ``snapshotbackup`` makes a full snapshot backup, separate from the
  regular backups.  Handy right before a big change in the site.

- ``snapshotrestore`` restores the latest full snapshot backup.

- ``zipbackup`` makes a zip backup.  This zips the Data.fs and puts
  the blobstorage in one tar archive, handy for copying production data
  to your local machine.  Enable this with ``PLONE_BACKUP_ENABLE_ZIPBACKUP=true``.

- ``ziprestore`` restores the latest zipbackup.

- ``altrestore`` restores from an alternative source, see
  `Alternative restore source`_.

You can run them directly, for example ``plone-backup snapshotbackup``,
or generate the familiar ``bin/backup``, ``bin/restore``, etcetera scripts
with ``plone-backup generate``.


Compatibility
-------------

``plone.backup`` is tested with Python 3.10-3.14.
In Plone terms it works fine on Plone 6.0, 6.1, 6.2.
It depends on ``ZODB``, which provides the ``repozo`` script.

Backing up the blobstorage uses ``rsync`` by default,
and archiving it uses ``tar``.
The ``incremental_blobs`` option needs GNU ``tar``.


Usage in a cookieplone project
------------------------------

Add ``plone.backup`` to the dependencies of your backend, for example in
``backend/pyproject.toml``, and install it.  Then, in the ``backend`` directory::

    uv run plone-backup backup

By default the filestorage is ``var/filestorage/Data.fs`` and the
blobstorage is ``var/blobstorage``, relative to the current directory.
Check the ``db_filestorage_location`` and ``db_blob_location`` in
``instance.yaml``.  With the default cookieplone settings the data is in
``instance/var``, so you put this in ``backend/.env``::

    PLONE_BACKUP_VAR_DIR=instance/var

Now ``uv run plone-backup backup`` backs up ``instance/var/filestorage/Data.fs``
to ``instance/var/backups``, and ``instance/var/blobstorage`` to
``instance/var/blobstoragebackups``.

If you prefer scripts, run ``uv run plone-backup generate``.
This creates ``bin/backup``, ``bin/snapshotbackup``, ``bin/restore`` and
``bin/snapshotrestore``, with the options of that moment baked in.
Run ``plone-backup generate`` again after changing an option.
Use ``--bin-dir`` or ``PLONE_BACKUP_BIN_DIR`` to put the scripts elsewhere.

Some ``Makefile`` targets you may want to add::

    .PHONY: backup
    backup: ## Backup the database
    	@uv run plone-backup backup

    .PHONY: snapshot
    snapshot: ## Make a snapshot backup of the database
    	@uv run plone-backup snapshotbackup

    .PHONY: restore
    restore: ## Restore the latest backup of the database
    	@uv run plone-backup restore


Docker image
------------

The ``Dockerfile`` builds an image that makes scheduled backups.
It runs `supercronic <https://github.com/aptible/supercronic>`_,
which passes the environment to the backup jobs, and logs their
output to the container log.

The image expects the data of Plone in ``/data``, as the
``plone/plone-backend`` and ``plone/plone-zeo`` images have it,
and writes the backups to ``/backups``.  It runs as user ``plone``
with uid 500, like those images, so it can read and restore their files.

These variables are only used by the image:

``PLONE_BACKUP_CRON``
    Cron schedule for the ``backup`` command.  Default in the image: ``0 3 * * *``.
    Set it to an empty string to disable it.
``PLONE_BACKUP_SNAPSHOT_CRON``
    Cron schedule for the ``snapshotbackup`` command.  Default: not set.

The image sets ``PLONE_BACKUP_VAR_DIR=/data`` and ``PLONE_BACKUP_LOCATIONPREFIX=/backups``.
All other options work as described below.

An example ``docker-compose.yml`` snippet, with ZEO::

    services:
      db:
        image: plone/plone-zeo:6
        volumes:
          - vol-site-data:/data

      backup:
        image: ghcr.io/plone/plone-backup:latest
        environment:
          PLONE_BACKUP_CRON: "0 3 * * *"
          PLONE_BACKUP_SNAPSHOT_CRON: "0 4 * * 0"
          PLONE_BACKUP_KEEP: 7
        volumes:
          - vol-site-data:/data
          - vol-backups:/backups

    volumes:
      vol-site-data: {}
      vol-backups: {}

You can also use ``env_file: backup.env`` instead of ``environment``.

Run a command once, for example a snapshot right before an update::

    docker compose run --rm backup snapshotbackup

To restore, first stop Plone, so nothing writes to the database::

    docker compose stop backend db
    docker compose run --rm backup restore
    docker compose start db backend

Without a terminal, for example in a script, add ``--no-prompt`` to skip
the confirmation question.  To restore the state at a certain date, pass
it like this: ``docker compose run --rm backup restore 2026-10-01-03-00``.

Build the image yourself with ``docker build -t plone-backup .``.

Note that ``/backups`` is a volume on the same machine as your data.
You should copy your backups to a different machine, or mount ``/backups``
from elsewhere.


Backed up data
--------------

Which data do we backup?

- The ZODB filestorage, by default located at ``var/filestorage/Data.fs``.

- The blobstorage, by default located at ``var/blobstorage``.

Which data do we *not* backup?  Everything else of course,
but specifically:

- Data stored in ``RelStorage`` will *not* be backed up.  You could
  still use this package to back up the filesystem blobstorage,
  possibly with the ``only_blobs`` option.
- Other data stored in SQL, perhaps via SQLAlchemy, will *not* be backed up.
- It does *not* create a backup of your project directory.


Backup
------

The ``backup`` command makes a normal incremental ``repozo`` backup of the
``Data.fs`` in ``var/backups``.  The blobstorage is backed up to
``var/blobstoragebackups``.

The ``snapshotbackup`` command places a full backup in ``var/snapshotbackups``,
and the blobs in ``var/blobstoragesnapshots``.  It does not interfere with
the regular backups.

The ``zipbackup`` command places a full backup in ``var/zipbackups``
and a tarball of the blobstorage in ``var/blobstoragezips``.
It overrides a few settings:

- ``archive_blob`` is turned on.
- ``keep`` is set to 1 to avoid keeping lots of needless backups.
- ``keep_blob_days`` is ignored because it is a full backup.


Restore
-------

The ``restore`` command restores the very latest normal incremental
``repozo`` backup and the blobstorage.
``snapshotrestore`` restores the latest snapshot backup,
``ziprestore`` the zipbackup.

You can also restore the backup as of a certain date. Pass a date argument.
According to ``repozo``: specify UTC (not local) time.
The format is ``yyyy-mm-dd[-hh[-mm[-ss]]]``.
So as a simple example, restore to 25 December 1972::

    plone-backup restore 1972-12-25

or to that same date, at 2,03 seconds past 1::

    bin/restore 1972-12-25-01-02-03

For blobs, we restore the directory from the first backup at or before the
specified date.

The restore commands ask for confirmation before starting the restore,
as this is a potentially dangerous command.  You need to explicitly type
``yes``.  With ``-n`` or ``--no-prompt`` you skip this question::

    This will replace the filestorage:
        /path/to/var/filestorage/Data.fs
    This will replace the blobstorage:
        /path/to/var/blobstorage
    Are you sure? (yes/No)?

Note that for large filestorages and blobstorages **it may take long to restore**.
You should do a test restore and check how long it takes.


Command line
------------

``plone-backup`` has these options and commands::

    plone-backup [-e ENV_FILE] COMMAND

    -e, --env-file  read PLONE_BACKUP_* variables from this file,
                    default: .env in the current directory, if it exists.
                    Variables in the environment win.

    backup, zipbackup, snapshotbackup,
    restore, ziprestore, snapshotrestore, altrestore
                    Run a backup or restore.  Options:
                    -q, --quiet: only show warnings and errors
                    -n, --no-prompt: do not ask for confirmation
                    and for the restore commands an optional date.
    generate        Generate scripts for the commands, see below.
    show            Show the computed options.
    crontab         Print a crontab, see `Docker image`_.

The ``-q`` option is useful in a cron job: you only get output when there is
a problem.  It also works for the generated scripts: ``bin/backup -q``.


Names of the scripts
--------------------

With ``PLONE_BACKUP_NAME`` you can change the name of the generated scripts,
and the default names of the backup directories.
With ``PLONE_BACKUP_NAME=plonebackup`` and ``PLONE_BACKUP_ENABLE_ZIPBACKUP=true``,
``plone-backup generate`` creates these scripts::

    bin/plonebackup
    bin/plonebackup-zip
    bin/plonebackup-snapshot
    bin/plonebackup-restore
    bin/plonebackup-ziprestore
    bin/plonebackup-snapshotrestore

And the backups go to ``var/plonebackups``, ``var/plonebackup-snapshots``,
etcetera.  Use several env files to generate several sets of scripts::

    plone-backup --env-file files.env generate
    plone-backup --env-file blobs.env generate

When you generate scripts again, scripts that we generated earlier
for the same name and are no longer wanted, are removed.  For example
``bin/zipbackup`` when you have switched off ``PLONE_BACKUP_ENABLE_ZIPBACKUP``.


Options
-------

None of the options are needed by default.
Each option is an environment variable: the option name in capitals,
with ``PLONE_BACKUP_`` in front.  So option ``keep`` is ``PLONE_BACKUP_KEEP``,
and ``blobbackuplocation`` is ``PLONE_BACKUP_BLOBBACKUPLOCATION``.
Boolean options accept ``true``, ``yes``, ``on`` and ``1`` as true,
everything else is false.

Relative paths are relative to ``PLONE_BACKUP_BASE_DIR``, by default the
current directory.  But relative paths in the ``location`` options
(``location``, ``snapshotlocation``, ``ziplocation``, ``blobbackuplocation``,
``blobsnapshotlocation``, ``blobziplocation``) are relative to the
``locationprefix``.  In paths, ``~`` (home dir) and ``$VARIABLE``-style
environment variables are expanded.

.. Note: keep this in alphabetical order please.

``alternative_restore_source``
    You can restore from an alternative source.  See `Alternative restore source`_.

``archive_blob``
    Use ``tar`` archiving functionality. ``false`` by default. Set it to ``true``
    and backup/restore will be done with the ``tar`` command.
    This option also works with snapshot backup/restore commands. As this
    counts as a full backup ``keep_blob_days`` is ignored.
    See the ``compress_blob`` option if you want to compress the archive.

``backup_blobs``
    Backup the blob storage.  Default is ``true``.
    If ``backup_blobs`` is false, ``enable_zipbackup`` cannot be true,
    because the ``zipbackup`` command is not useful then.

``base_dir``
    Directory that relative paths are relative to.
    Default: the current directory.

``bin_dir``
    Directory for the scripts that ``plone-backup generate`` creates.
    Default: ``bin``.

``blob_storage``
    Location of the directory where the blobs (binary large objects)
    are stored.  Default: ``blobstorage`` in the ``var_dir``.

``blob_timestamps``
    Default is true.
    If false, we create ``blobstorage.0``.
    The next time, we rotate this to ``blobstorage.1`` and create a new ``blobstorage.0``.
    With ``blob_timestamps = true``, we create stable directories that we do not rotate.
    They get a timestamp, the same timestamp that the ZODB filestorage backup gets.
    For example: ``blobstorage.1972-12-25-01-02-03``.
    Or with ``archive_blob = true``: ``blobstorage.1972-12-25-01-02-03.tar``.
    We create a ``latest`` symlink to the most recent backup.
    Blob timestamps are not used with zipbackup, because this only keeps 1 backup.
    Setting this to false is deprecated.

``blobbackuplocation``
    Directory where the blob storage will be backed up to.  Defaults
    to ``blobstoragebackups`` in the ``locationprefix``.

``blobsnapshotlocation``
    Directory where the blob storage snapshots will be created.
    Defaults to ``blobstoragesnapshots`` in the ``locationprefix``.

``blobziplocation``
    Directory where the blob storage zipbackups will be created.
    Defaults to ``blobstoragezips`` in the ``locationprefix``.

``compress_blob``
    Default is false.
    This is only used when the ``archive_blob`` option is true.
    When switched on, it will compress the archive,
    resulting in a ``.tar.gz`` instead of a ``tar`` file.
    When restoring, we always look for both compressed and normal archives.
    In most cases compressing hardly decreases the size, and it takes long.

``datafs``
    Location of the filestorage.
    Default: ``filestorage/Data.fs`` in the ``var_dir``.

``debug``
    In rare cases when you want to know exactly what's going on, set debug to
    ``true`` to get debug level logging. ``repozo`` is also run
    with ``--verbose`` if this option is enabled.

``enable_snapshotrestore``
    Default: true.  A ``snapshotrestore`` command is very useful in development
    environments, but can be harmful in production.
    If you don't want it, set this option to false.

``enable_zipbackup``
    Enable the ``zipbackup`` and ``ziprestore`` commands.  Default: false.

``full``
    By default, incremental backups are made. If this option is set to ``true``,
    ``backup`` will always make a full backup.

``incremental_blobs``
    Default is false.
    When switched on, it will use the ``--listed-incremental`` option of ``tar``.
    Note: this only works with the GNU version of ``tar``.
    On Mac you may need to install this with ``brew install gnu-tar`` and change your ``PATH`` according to the instructions.
    It will create a metadata or `snapshot file <https://www.gnu.org/software/tar/manual/html_node/Incremental-Dumps.html>`_
    so that a second backup will create a second tarball with only the differences.
    This option is ignored when the ``archive_blob`` option is false.
    This option *requires* the ``blob_timestamps`` option to be true.
    Note that the ``latest`` symlink to the most recent backup is not created with ``incremental_blobs`` true.
    For large blobstorages it may take long to restore, so do test it out.

``keep``
    Number of full backups to keep. Defaults to ``2``, which means that the
    current and the previous full backup are kept. Older backups are removed,
    including their incremental backups. Set it to ``0`` to keep all backups.

``keep_blob_days``
    Number of *days* of blob backups to keep.  Defaults to ``14``, so
    two weeks.  This is **only** used when ``only_blobs`` is true and
    ``full`` is false.  Otherwise we remove the blob backups that have
    no matching filestorage backup.

``location``
    Location where backups are stored. Defaults to ``backups`` in the ``locationprefix``.

``locationprefix``
    Location of the folder where all other backup and snapshot folders will
    be created. Defaults to the ``var_dir``.
    Note that this does not influence where we look for a source filestorage or blobstorage.

``name``
    Name of the scripts and default backup directories, see `Names of the scripts`_.
    Default: ``backup``.

``only_blobs``
    Only backup the blobstorage, not the ``Data.fs`` filestorage.  False
    by default.  May be a useful option if for example you want one set of
    scripts for the filestorage and one for the blobstorage, using
    ``only_blobs`` in one and ``backup_blobs`` in the other.

``post_command``
    Command to execute after the backup has finished.  One use case
    would be to unmount the remote file system that you mounted
    earlier using the ``pre_command``.

``pre_command``
    Command to execute before starting the backup or restore.
    One use case would be to mount a remote file system using NFS or sshfs and put the
    backup there.  Any output will be printed.  If the command fails, we quit with
    an error.  Use ``&&`` or ``;`` to run multiple commands.

``repozo``
    The ``repozo`` script to use.  By default we look in the ``bin_dir``,
    next to the Python that runs ``plone-backup``, and on the ``PATH``.

``rsync_hard_links_on_first_copy``
    When using ``rsync``, the blob files for the first backup are copied
    and then subsequent backups make use of hard links from this initial
    copy, to save time and disk space.
    Enable this option to also use hard links for the initial copy to further reduce
    disk usage.
    This is safe for ZODB blobs, since they are not modified in place.
    The ``blob_storage`` and the ``blobbackuplocation``
    have to be in the same partition for hard links to be possible.

``rsync_options``
    Add extra options to the default ``rsync -a`` command. Default is no
    extra parameters. This can be useful for example when you want to restore
    a backup from a symlinked directory, in which case
    ``--no-l -k`` does the trick.

``snapshotlocation``
    Location where snapshot backups of the filestorage are stored. Defaults to
    ``snapshotbackups`` in the ``locationprefix``.

``use_rsync``
    Use ``rsync`` with hard links for backing up the blobs.  Default is
    true.  When you set this to false, we fall back to a simple copy.

``var_dir``
    The directory with the data of Plone.  Default: ``var``.
    The defaults of ``datafs``, ``blob_storage`` and ``locationprefix`` are in here.

``ziplocation``
    Location where zip backups of the filestorage are stored. Defaults to
    ``zipbackups`` in the ``locationprefix``.

An example ``.env`` file using various options::

    PLONE_BACKUP_LOCATION=/var/backups/myproject
    PLONE_BACKUP_KEEP=2
    PLONE_BACKUP_DATAFS=subfolder/myproject.fs
    PLONE_BACKUP_FULL=true
    PLONE_BACKUP_DEBUG=true
    PLONE_BACKUP_SNAPSHOTLOCATION=snap/my
    PLONE_BACKUP_PRE_COMMAND=echo 'Can I have a backup?'
    PLONE_BACKUP_POST_COMMAND=echo 'Thanks a lot for the backup.' && echo 'We are done.'

In a ``.env`` file, values may be quoted.  In double quotes, ``\n`` is a newline.

If you see a warning about an unknown variable, check for typos:
``PLONE_BACKUP_KEPE`` is ignored.


Blob storage
------------

Plone uses a blob storage to store files (Binary Large OBjects) on the file system.
We back it up by default.

You can choose to *only* backup blobs, or specifically *not* backup the blobs,
for example to make separate scripts::

    # files.env
    PLONE_BACKUP_NAME=filebackup
    PLONE_BACKUP_BACKUP_BLOBS=false

    # blobs.env
    PLONE_BACKUP_NAME=blobbackup
    PLONE_BACKUP_ONLY_BLOBS=true

With these files, ``plone-backup --env-file files.env backup`` only backs up the filestorage
and ``plone-backup --env-file blobs.env backup`` only backs up the blobstorage.


rsync
-----

By default we use ``rsync`` to create backups.  We create hard links
with this tool, to save disk space and still have incremental backups.
This probably requires a unixy (Linux, macOS) operating system.

It is based on this article by Mike Rubel:
http://www.mikerubel.org/computers/rsync_snapshots/

We have not tried this on Windows.  Reports are welcome, but best is
probably to set ``PLONE_BACKUP_USE_RSYNC=false``.
Then we simply copy the blobstorage directory.


Alternative restore source
--------------------------

You can restore from an alternative source.  Use case: first make a
backup of your production site, then go to the testing or staging
server and restore the production data there.

In the ``alternative_restore_source`` option you can define the
filestorage and blobstorage backup source directories using this syntax::

    PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=Data datafs_backup [blobdir_backup]

The first word must be ``Data`` (or ``1``) for the standard ``Data.fs``.
This enables the ``altrestore`` command.  For example::

    PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=Data /path/to/production/var/backups /path/to/production/var/blobstoragebackups

This uses ``repozo`` to restore the Data.fs from
the ``/path/to/production/var/backups`` repository to the standard
``var/filestorage/Data.fs`` location.  It copies the most recent
blobstorage backup from ``/path/to/production/var/blobstoragebackups/``
to the standard ``var/blobstorage`` location.

Calling it with a specific date is supported just like the normal restore::

    plone-backup altrestore 2000-12-31-23-59


Migrating from collective.recipe.backup
---------------------------------------

The options are the same, with these differences:

- Options are environment variables: ``keep = 3`` becomes ``PLONE_BACKUP_KEEP=3``.
- The name of the buildout part is the ``name`` option.
- We do not look in other buildout parts for the location of the filestorage
  and blobstorage.  Set ``var_dir``, or ``datafs`` and ``blob_storage``.
- ``blob_storage`` defaults to ``blobstorage`` in the ``var_dir``.
- ``blob-storage`` and ``alternative_restore_sources`` are no longer supported:
  use ``blob_storage`` and ``alternative_restore_source``.
- Paths can not use ``${buildout:directory}``.  Use relative paths, or
  environment variables, for example ``$PWD/backups``.
- Multi-line values like several ``pre_command`` lines: use ``&&``.
- Instead of a part with ``z3c.recipe.usercrontab``, use the Docker image
  or your own crontab.


Development
-----------

- Code repository: https://github.com/plone/plone.backup

- Issue tracker: https://github.com/plone/plone.backup/issues

- The history before version 1.0 is the history of ``collective.recipe.backup``:
  https://github.com/collective/collective.recipe.backup

- Run the tests with ``tox``, or with ``pytest`` after
  ``pip install -e '.[test]'``.
  The tests in ``src/plone/backup/tests/*.rst`` are good reading if you
  are wondering about the effect some options have.

- Questions and comments to https://community.plone.org.
