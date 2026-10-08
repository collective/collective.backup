# -*-doctest-*-

Locationprefix option
=====================

The locationprefix options allows you to set a base folder for all your backups and snapshot folders, instead of modifying all location options.

The simplest way to use it is to add it in ``.env`` like this::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_LOCATIONPREFIX=backuplocation
    ... """)

Let's generate the scripts::

    >>> ignore = system(generate)

Untested in this file, as it would create directories in your root or your
home dir, are absolute links (starting with a '/') or directories in your home
dir or relative (``../``) path. They do work, of course. Also ``~`` and
``$BACKUP``-style environment variables are expanded.


Backup
------

Calling ``bin/backup`` results in a normal repozo backup.
We have put in place a mock repozo script that prints the options it is passed.

By default, backups are done in ``backuplocation/backups``::

    >>> print(system('bin/backup'))
    INFO: Created /sample-project/backuplocation/backups
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/backuplocation/backups
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/backups --quick --gzip


Restore
-------

You can restore the very latest backup with ``bin/restore``.
This will create the target directory when it does not exist::

    >>> ls('backuplocation')
    d  backups
    >>> print(system('bin/restore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Created directory /sample-project/var/filestorage
    INFO: Please wait while restoring database file: /sample-project/backuplocation/backups to /sample-project/var/filestorage/Data.fs
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/backups
    >>> ls('backuplocation')
    d  backups
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
    INFO: Please wait while restoring database file: /sample-project/backuplocation/backups to /sample-project/var/filestorage/Data.fs
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/backups -D 1972-12-25

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
    INFO: Created /sample-project/backuplocation/snapshotbackups
    INFO: Please wait while making snapshot backup: /sample-project/var/filestorage/Data.fs to /sample-project/backuplocation/snapshotbackups
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/snapshotbackups -F --gzip

You can restore the very latest snapshotbackup with ``bin/snapshotrestore``::

    >>> print(system('bin/snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/backuplocation/snapshotbackups to /sample-project/var/filestorage/Data.fs
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/snapshotbackups


Prefix plus relative locations
------------------------------

A prefix plus relative locations should result in locations relative to the prefix.

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_BACKUP_BLOBS=true
    ... PLONE_BACKUP_ENABLE_ZIPBACKUP=true
    ... PLONE_BACKUP_LOCATIONPREFIX=backuplocation
    ... PLONE_BACKUP_LOCATION=std/datafs
    ... PLONE_BACKUP_BLOBBACKUPLOCATION=std/blobs
    ... PLONE_BACKUP_SNAPSHOTLOCATION=snapshots/datafs
    ... PLONE_BACKUP_BLOBSNAPSHOTLOCATION=snapshots/blobs
    ... PLONE_BACKUP_ZIPLOCATION=snapshots/zip
    ... PLONE_BACKUP_BLOBZIPLOCATION=snapshots/zipblobs
    ... """)
    >>> mkdir('var', 'blobstorage')
    >>> write('var', 'blobstorage', 'blob.txt', 'dummy blob')

Let's generate the scripts::

    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/zipbackup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/ziprestore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    <BLANKLINE>

Mock some repozo backups with timestamps.
In this way we can check that our logic for matching a blobstorage backup and filestorage backup works.
And it is easier to write the tests with a real date rather than 20...-...-...-...-...-...

    >>> mkdir('backuplocation', 'std')
    >>> mkdir('backuplocation', 'std', 'datafs')
    >>> write('backuplocation', 'std', 'datafs', '1999-12-31-01-01-01.fsz', 'mock datafs backup')
    >>> mkdir('backuplocation', 'snapshots')
    >>> mkdir('backuplocation', 'snapshots', 'datafs')
    >>> write('backuplocation', 'snapshots', 'datafs', '1999-10-01-01-01-01.fsz', 'mock datafs snapshotbackup')

And run the scripts::

    >>> print(system('bin/backup'))
    INFO: Created /sample-project/backuplocation/std/blobs
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/backuplocation/std/datafs
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/backuplocation/std/blobs
    INFO: rsync -a  /sample-project/var/blobstorage /sample-project/backuplocation/std/blobs/blobstorage.1999-12-31-01-01-01
    INFO: Creating symlink from latest to blobstorage.1999-12-31-01-01-01
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/std/datafs --quick --gzip
    >>> ls('backuplocation', 'std', 'blobs')
    d  blobstorage.1999-12-31-01-01-01
    d  latest
    >>> ls('backuplocation', 'std', 'blobs', 'blobstorage.1999-12-31-01-01-01')
    d  blobstorage
    >>> ls('backuplocation', 'std', 'blobs', 'blobstorage.1999-12-31-01-01-01', 'blobstorage')
    -  blob.txt
    >>> print(system('bin/zipbackup'))
    INFO: Created /sample-project/backuplocation/snapshots/zip
    INFO: Created /sample-project/backuplocation/snapshots/zipblobs
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/backuplocation/snapshots/zip
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/backuplocation/snapshots/zipblobs
    INFO: tar cf /sample-project/backuplocation/snapshots/zipblobs/blobstorage.0.tar  -C /sample-project/var/blobstorage .
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/snapshots/zip -F --gzip
    >>> print(system('bin/snapshotbackup'))
    INFO: Created /sample-project/backuplocation/snapshots/blobs
    INFO: Please wait while making snapshot backup: /sample-project/var/filestorage/Data.fs to /sample-project/backuplocation/snapshots/datafs
    INFO: Please wait while making snapshot of blobs from /sample-project/var/blobstorage to /sample-project/backuplocation/snapshots/blobs
    INFO: rsync -a  /sample-project/var/blobstorage /sample-project/backuplocation/snapshots/blobs/blobstorage.1999-10-01-01-01-01
    INFO: Creating symlink from latest to blobstorage.1999-10-01-01-01-01
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/snapshots/datafs -F --gzip
    >>> print(system('bin/restore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/backuplocation/std/datafs to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/backuplocation/std/blobs to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/backuplocation/std/blobs/blobstorage.1999-12-31-01-01-01/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/std/datafs
    >>> print(system('bin/ziprestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/backuplocation/snapshots/zip to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/backuplocation/snapshots/zipblobs to /sample-project/var/blobstorage
    INFO: Removing /sample-project/var/blobstorage
    INFO: Extracting /sample-project/backuplocation/snapshots/zipblobs/blobstorage.0.tar to /sample-project/var/blobstorage
    INFO: tar xf /sample-project/backuplocation/snapshots/zipblobs/blobstorage.0.tar  -C /sample-project/var/blobstorage
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/snapshots/zip
    >>> print(system('bin/snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/backuplocation/snapshots/datafs to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/backuplocation/snapshots/blobs to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/backuplocation/snapshots/blobs/blobstorage.1999-10-01-01-01-01/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/backuplocation/snapshots/datafs


Prefix plus absolute locations
------------------------------

A prefix plus absolute locations should result in ignoring the prefix.

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_BACKUP_BLOBS=true
    ... PLONE_BACKUP_LOCATIONPREFIX=backuplocation
    ... PLONE_BACKUP_LOCATION=$PWD/myownbackup/datafs
    ... PLONE_BACKUP_BLOBBACKUPLOCATION=$PWD/myownbackup/blobs
    ... """)

Let's generate the scripts::

    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    Removed script '/sample-project/bin/zipbackup'.
    Removed script '/sample-project/bin/ziprestore'.
    >>> mkdir('myownbackup')
    >>> mkdir('myownbackup', 'datafs')
    >>> write('myownbackup', 'datafs', '1999-08-01-01-01-01.fsz', 'mock datafs snapshotbackup')

And run the scripts::

    >>> print(system('bin/backup'))
    INFO: Created /sample-project/myownbackup/blobs
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/myownbackup/datafs
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/myownbackup/blobs
    INFO: rsync -a  /sample-project/var/blobstorage /sample-project/myownbackup/blobs/blobstorage.1999-08-01-01-01-01
    INFO: Creating symlink from latest to blobstorage.1999-08-01-01-01-01
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/myownbackup/datafs --quick --gzip


Names of created scripts
------------------------

The name will normally be ``backup``, leading to a
``bin/backup`` and ``bin/snapshotbackup``.  Should you set the ``name``
option to something else, the script names will also be different as will
the created ``var/`` directories:

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_NAME=plonebackup
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_LOCATIONPREFIX=backuplocation
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/plonebackup'.
    Generated script '/sample-project/bin/plonebackup-snapshot'.
    Generated script '/sample-project/bin/plonebackup-restore'.
    Generated script '/sample-project/bin/plonebackup-snapshotrestore'.
    <BLANKLINE>

Note that the ``restore``, ``snapshotbackup`` and ``snapshotrestore`` script name used when the
name is ``backup`` is now prefixed with the name:

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

In the backuplocation/ directory, the existing backups and snapshotbackups directories
are still present.  We of course never remove that kind of directory!
The different name *did* result in two directories named after it:

    >>> ls('backuplocation')
    d  backups
    d  snapshotbackups
    d  snapshots
    d  std
