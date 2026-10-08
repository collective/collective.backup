# -*-doctest-*-

Example usage
=============

The simplest way to use it is to add a part in ``.env`` like this::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... """)

Running the buildout adds a backup, snapshotbackup, restore and
snapshotrestore scripts to the ``bin/`` directory and, by default, it
creates the ``var/backups`` and ``var/snapshotbackups`` dirs::

    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    <BLANKLINE>
    >>> ls('bin')
    -  backup
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore

Backup
------

Calling ``bin/backup`` results in a normal repozo backup. We put in place a
mock repozo script that prints the options it is passed (and make it
executable). It is horridly unix-specific at the moment.

By default, backups are done in ``var/backups``::

    >>> print(system('bin/backup'))
    INFO: Created /sample-project/var/backups
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/var/backups
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups --quick --gzip


Restore
-------

You can restore the very latest backup with ``bin/restore``.
This will create the target directory when it does not exist::

    >>> ls('var')
    d  backups
    >>> print(system('bin/restore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Created directory /sample-project/var/filestorage
    INFO: Please wait while restoring database file: /sample-project/var/backups to /sample-project/var/filestorage/Data.fs
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups
    >>> ls('var')
    d  backups
    d  filestorage
    >>> ls('var' , 'filestorage')

You can also restore the backup as of a certain date. Just pass a date
argument. According to repozo: specify UTC (not local) time.  The format is
``yyyy-mm-dd[-hh[-mm[-ss]]]``.

    >>> print(system('bin/restore 1972-12-25', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at 1972-12-25.
    INFO: Please wait while restoring database file: /sample-project/var/backups to /sample-project/var/filestorage/Data.fs
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups -D 1972-12-25

Note that restoring a blobstorage to a specific date only works since
release 2.3.  We will test that a bit further on.


Snapshots
---------

For quickly grabbing the current state of a production database so you can
download it to your development laptop, you want a full backup. But
you shouldn't interfere with the regular backup regime. Likewise, a quick
backup just before updating the production server is a good idea. For that,
the ``bin/snapshotbackup`` is great. It places a full backup in, by default,
``var/snapshotbackups``.

    >>> print(system('bin/snapshotbackup'))
    INFO: Created /sample-project/var/snapshotbackups
    INFO: Please wait while making snapshot backup: /sample-project/var/filestorage/Data.fs to /sample-project/var/snapshotbackups
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/snapshotbackups -F --gzip

You can restore the very latest snapshotbackup with ``bin/snapshotrestore``::

    >>> print(system('bin/snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/var/snapshotbackups to /sample-project/var/filestorage/Data.fs
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/snapshotbackups


Names of created scripts
------------------------

A backup part will normally be called ``[backup]``, leading to a
``bin/backup`` and ``bin/snapshotbackup``.  Should you name your part
something else,  the script names will also be different as will the created
``var/`` directories (since version 1.2):

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_NAME=plonebackup
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/plonebackup'.
    Generated script '/sample-project/bin/plonebackup-snapshot'.
    Generated script '/sample-project/bin/plonebackup-restore'.
    Generated script '/sample-project/bin/plonebackup-snapshotrestore'.
    <BLANKLINE>

Note that the ``restore``, ``snapshotbackup`` and ``snapshotrestore`` script name used when the
name is ``[backup]`` is now prefixed with the part name:

    >>> ls('bin')
    -  backup
    -  plonebackup
    -  plonebackup-restore
    -  plonebackup-snapshot
    -  plonebackup-snapshotrestore
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore

In the var/ directory, the existing backups and snapshotbackups directories
are still present.  The recipe of course never removes that kind of directory!
The different part name *did* result in two directories named after the part:

    >>> ls('var')
    d  backups
    d  filestorage
    d  snapshotbackups
